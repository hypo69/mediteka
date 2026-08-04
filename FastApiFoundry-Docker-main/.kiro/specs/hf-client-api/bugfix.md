# Bugfix Requirements Document

## Introduction

`src/models/hf_client.py` contains three bugs where the `HFClient` class uses fragile
manual filesystem scanning instead of official HuggingFace library APIs, and is missing
chat template support for instruction-tuned models.

**Bug 1 — `list_downloaded()`** manually parses the internal HuggingFace cache directory
structure (`models--author--name/snapshots/hash/`) instead of using the official
`scan_cache_dir()` API. This breaks silently if HuggingFace changes its cache layout.

**Bug 2 — `load_model()`** manually navigates `models--author--name/snapshots/` to find
the latest snapshot hash directory instead of using `snapshot_download(local_files_only=True)`,
which is the official API for resolving a cached model path without network access.

**Bug 3 — `generate()`** passes the raw prompt string directly to the pipeline without
applying a chat template. Modern instruction-tuned models (Qwen, Llama, Gemma, Mistral)
require the prompt to be formatted with their specific chat template (e.g.
`<|im_start|>user\n...<|im_end|>`) to produce correct responses. Skipping this step
significantly degrades response quality.

All three fixes must preserve the existing public API signatures and return shapes.
Fallback behaviour must be retained so that failures in the new API paths gracefully
revert to the current filesystem-based logic.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `list_downloaded()` is called THEN the system manually iterates the cache
    directory, filters entries whose names start with `models--`, and parses the
    `models--author--name` directory name to reconstruct the model ID — relying on
    HuggingFace's internal cache layout instead of the official `scan_cache_dir()` API.

1.2 WHEN `list_downloaded()` encounters a cache layout change introduced by a future
    version of `huggingface_hub` THEN the system silently returns an empty list or
    incorrect model IDs without raising an error.

1.3 WHEN `load_model()` is called with a model that is present in the local cache THEN
    the system manually constructs the path `<base>/models--<author>--<name>/snapshots/`
    and picks the first subdirectory as the snapshot path — relying on HuggingFace's
    internal directory structure instead of the official `snapshot_download(local_files_only=True)` API.

1.4 WHEN `load_model()` is called and the snapshot directory contains more than one hash
    subdirectory THEN the system picks `dirs[0]` (filesystem order) rather than the
    correct latest snapshot, potentially loading a stale model revision.

1.5 WHEN `generate()` is called with an instruction-tuned model (e.g. Qwen, Llama,
    Gemma, Mistral) THEN the system passes the raw prompt string directly to the
    pipeline without applying the model's chat template, causing the model to receive
    unformatted text instead of the expected structured message format.

1.6 WHEN `generate()` is called with a model whose tokenizer defines a `chat_template`
    THEN the system ignores the template, resulting in degraded response quality and
    off-format outputs from instruction-tuned models.

---

### Expected Behavior (Correct)

2.1 WHEN `list_downloaded()` is called THEN the system SHALL use `scan_cache_dir()` from
    `huggingface_hub` to enumerate cached repositories, reading `repo.repo_id`,
    `repo.size_on_disk`, and `repo.nb_snapshots` from the returned `CacheInfo` object.

2.2 WHEN `scan_cache_dir()` raises an exception THEN the system SHALL fall back to the
    existing filesystem scan so that `list_downloaded()` continues to return results
    even if the official API is unavailable.

2.3 WHEN `list_downloaded()` returns results THEN the system SHALL return a list of dicts
    each containing exactly the keys `{"id", "path", "loaded", "size_mb", "source"}`,
    identical in shape to the current return value.

2.4 WHEN `load_model()` is called with a model that is present in the local cache THEN
    the system SHALL use `snapshot_download(repo_id=model_id, local_files_only=True,
    cache_dir=str(HF_MODELS_DIR))` to resolve the correct local snapshot path without
    making any network requests.

2.5 WHEN `snapshot_download(local_files_only=True)` raises an exception (e.g. model not
    in cache) THEN the system SHALL fall back to the existing manual snapshot directory
    search so that `load_model()` continues to work for models stored in non-standard
    locations.

2.6 WHEN `load_model()` resolves a local path via either method THEN the system SHALL
    accept `model_id` and `device` as parameters and return a dict with keys
    `{"success", "model_id", "device"}`, identical in shape to the current return value.

2.7 WHEN `generate()` is called and the loaded model's tokenizer has both an
    `apply_chat_template` method and a non-empty `chat_template` attribute THEN the
    system SHALL format the prompt as `[{"role": "user", "content": prompt}]` using
    `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`
    before passing it to the pipeline.

2.8 WHEN `generate()` is called and the tokenizer does not have `apply_chat_template` or
    has an empty `chat_template` THEN the system SHALL pass the raw prompt string to the
    pipeline unchanged, preserving backward compatibility with base (non-instruct) models.

2.9 WHEN `generate()` returns a result THEN the system SHALL return a dict with keys
    `{"success", "content", "model"}`, identical in shape to the current return value.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `list_downloaded()` is called and the cache contains models downloaded via the
    standard `snapshot_download` workflow THEN the system SHALL CONTINUE TO return those
    models in the result list with correct `id`, `path`, `loaded`, `size_mb`, and
    `source` values.

3.2 WHEN `list_downloaded()` is called and `HF_MODELS_DIR` differs from the default
    `~/.cache/huggingface/hub` THEN the system SHALL CONTINUE TO scan both directories
    and deduplicate results by model ID.

3.3 WHEN `load_model()` is called with a `model_id` that is already present in
    `_loaded_models` THEN the system SHALL CONTINUE TO return
    `{"success": True, "model_id": model_id, "status": "already_loaded"}` without
    reloading.

3.4 WHEN `load_model()` is called with `device="auto"`, `"cpu"`, or `"cuda"` THEN the
    system SHALL CONTINUE TO pass the device parameter to `AutoModelForCausalLM.from_pretrained`
    via `device_map`.

3.5 WHEN `generate()` is called with a base (non-instruct) model whose tokenizer has no
    `chat_template` THEN the system SHALL CONTINUE TO pass the raw prompt to the pipeline
    and return a valid `{"success": True, "content": ..., "model": ...}` response.

3.6 WHEN `generate()` is called with `temperature`, `max_new_tokens`, `prompt`, and
    `model_id` parameters THEN the system SHALL CONTINUE TO accept those exact parameter
    names and forward them to the pipeline unchanged.

3.7 WHEN `download_model()` is called THEN the system SHALL CONTINUE TO use
    `snapshot_download` (with network access) and return `{"success", "model_id", "path"}`,
    unaffected by any changes to `list_downloaded()` or `load_model()`.

3.8 WHEN `unload_model()` is called for a loaded model THEN the system SHALL CONTINUE TO
    remove the model from `_loaded_models`, run garbage collection, and clear the CUDA
    cache if available.

3.9 WHEN the public API endpoints in `src/api/endpoints/hf_models.py` call
    `hf_client.list_downloaded()`, `hf_client.load_model()`, or `hf_client.generate()`
    THEN the system SHALL CONTINUE TO receive the same response shapes as before,
    requiring no changes to the endpoint layer.
