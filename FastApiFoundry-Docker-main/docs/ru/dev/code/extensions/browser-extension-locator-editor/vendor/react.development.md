# React.Development

**Файл:** `extensions/browser-extension-locator-editor/vendor/react.development.js`  
**Тип:** `.js`

---

### `appendInitialChild`

### `GwtWorkarounds`

Forked from fbjs/warning:
 * https://github.com/facebook/fbjs/blob/e66ba20ad5be433eb54423f2b097d829324d9de6/packages/fbjs/src/warning.js
 *
 * Only uses console.error for message disclosure.
 * MIT licensed

### `JsxNumberCoercion`

Coerces a string to a number, run-time checking for
 * non-finites. This is safe to use with strings that can be coerced to
 * numbers.

### `isEventSupported`

Similar to invariant but only logs a warning if the condition is not met.
 * This can be used to log issues in development environments in critical
 * paths. Removing the logging code for production environments will keep the
 * same logic and follow the same code paths.

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

### `ReactElement`

Use to restore the stack after a throw.

| Параметр | Тип | Описание |
|---|---|---|
| `type` | `*` | * @param {*} props |
| `key` | `*` | * @param {string|object} ref |
| `owner` | `*` | * @param {*} self A *temporary* helper to detect places where `this` is |
| `source` | `object` | An annotation object (added by a transpiler). |

### `jsx`

https://github.com/reactjs/rfcs/pull/107
 *

| Параметр | Тип | Описание |
|---|---|---|
| `type` | `*` | * @param {object} props |
| `key` | `string` | */ |

### `jsxDEV`

https://github.com/reactjs/rfcs/pull/107
 *

| Параметр | Тип | Описание |
|---|---|---|
| `type` | `*` | * @param {object} props |
| `key` | `string` | */ |

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

### `getRootHostContext`

### `getChildHostContext`

### `prepareForCommit`

### `resetAfterCommit`

### `createInstance`

### `appendInitialChild$1`

### `finalizeInitialChildren`

### `prepareUpdate`

### `shouldSetTextContent`

### `shouldDeprioritizeSubtree`

### `createTextInstance`

### `scheduleDeferredCallback`

### `cancelDeferredCallback`

### `setTimeout$1`

### `clearTimeout$1`

### `commitMount`

### `commitUpdate`

### `resetTextContent`

### `commitTextUpdate`

### `appendChild`

### `appendChildToContainer`

### `insertBefore`

### `insertInContainerBefore`

### `removeChild`

### `removeChildFromContainer`

### `hideInstance`

### `hideTextInstance`

### `unhideInstance`

### `unhideTextInstance`

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

### `getComponentNameFromType`

### `getContextName`

### `hasValidRef`

### `hasValidKey`

### `defineKeyPropWarningGetter`

### `defineRefPropWarningGetter`

### `getComponentNameFromType$1`

### `getWrappedName$1`

### `adoptClassInstance`

### `constructClassInstance`

### `callComponentWillMount`

### `callComponentWillReceiveProps`

### `Component`

### `checkShouldComponentUpdate`

### `applyDerivedStateFromProps`

### `areHookInputsEqual$1`

### `getIsUpdatingOpaqueValueInRenderPhase`

### `currentlyRenderingFiber$1`

### `createPortal`

### `getOwner`

### `getFiberCurrentPropsFromNode`

### `updateFiberProps`

### `requestCurrentTransition`

### `checkPropTypes`

### `lazy`

### `forwardRef`

### `isValidElement`

### `memo`

### `cache`

### `use`

### `startTransition`

### `unstable_act`

### `createContext`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
