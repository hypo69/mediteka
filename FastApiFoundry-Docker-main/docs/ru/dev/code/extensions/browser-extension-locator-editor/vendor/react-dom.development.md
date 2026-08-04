# React Dom.Development

**Файл:** `extensions/browser-extension-locator-editor/vendor/react-dom.development.js`  
**Тип:** `.js`

---

### `appendInitialChild`

### `JsxNumberCoercion`

Coerces a string to a number, run-time checking for
 * non-finites. This is safe to use with strings that can be coerced to
 * numbers.

### `get`

Similar to invariant but only logs a warning if the condition is not met.
 * This can be used to log issues in development environments in critical
 * paths. Removing the logging code for production environments will keep the
 * same logic and follow the same code paths.

### `isEventSupported`

Checks if an event is supported in the current execution environment.
 *
 * NOTE: This will not work correctly for non-generic events such as `change`,
 * `reset`, `load`, `error`, and `select`.
 *
 * Borrows from Modernizr.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `eventNameSuffix` | `string` | Event name, e.g. "click". |

### `precacheFiberNode`

`charCode` represents the actual numeric value of the key that was pressed.
 *
 * `key` is the string value of the key that was pressed.
 *
 * `keyCode` is a numeric value that represents the key that was pressed.
 * It is often the same as `charCode` but has many inconsistencies.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `hostInst` | `DOMElement` | The instance of a DOM element. |
| `node` | `Fiber` | The fiber node to store. |

### `getClosestInstanceFromNode`

Given a DOM node, return the closest HostComponent or HostText fiber ancestor.
 * If the target node is being mounted, such that it has not yet been assigned
 * a parent, we must search up the DOM tree to find the parent fiber.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `targetNode` | `DOMNode` | The DOM node to search from. |

### `frameYieldMs`

### `priorityLevelToFrameYieldMs`

### `runWithPriority`

### `shouldYield`

### `getIteratorFn`

### `disabledLog`

### `disableLogs`

### `reenableLogs`

### `describeBuiltInComponentFrame`

### `describeNativeComponentFrame`

### `describeClassComponentFrame`

### `describeFunctionComponentFrame`

### `getStackByComponentStackNode`

### `describeComponentFrame`

### `getPublicInstance`

### `getInstanceFromNode`

### `findHostInstanceByFiber`

### `emptyFindFiberByHostInstance`

### `getCurrentFiberForDevTools`

### `resolveCurrentlyRenderingComponent`

### `areHookInputsEqual`

### `isTextInputElement`

### `getEventKey`

### `isArray`

### `getLowestPriority`

### `getHighestPriority`

### `lanesToPriority`

### `captureCommitHook`

### `isActing`

### `getActingScope`

### `requestCurrentTransition`

### `getFiberCurrentPropsFromNode`

### `updateFiberProps`

### `getContextForSubtree`

### `createRoot`

### `hydrateRoot`

### `render`

### `unstable_renderSubtreeIntoContainer`

### `unmountComponentAtNode`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
