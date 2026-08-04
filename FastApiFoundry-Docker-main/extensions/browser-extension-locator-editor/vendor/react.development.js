/**
 * @license React
 * react.development.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
'use strict';
if (process.env.NODE_ENV !== "production") {
  (function() {
'use strict';

// TODO: This is a temporary fork of the react-dom/client entry point.
// Figure out how to allow multiple renderers to share the same client entry point.

var React = require('react');

var ReactSharedInternals = React.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;

// by calls to these methods by a Babel plugin.
//
// In PROD (or in packages without access to React internals),
// they are determined dynamically.
var ReactCurrentDispatcher = ReactSharedInternals.ReactCurrentDispatcher;
var ReactCurrentBatchConfig = ReactSharedInternals.ReactCurrentBatchConfig;
var ReactCurrentOwner = ReactSharedInternals.ReactCurrentOwner;
var ReactDebugCurrentFrame = ReactSharedInternals.ReactDebugCurrentFrame;
var IsSomeRendererActing = ReactSharedInternals.IsSomeRendererActing;

// Eagerly attach this to GWT, if it exists.
// Overcomes an issue that GWT bundled on i.frames doesn't get scheduled
// efficiently.
if (typeof __gwt_schedulehandled !== 'undefined' && typeof __gwt_schedulehandled.then === 'function') {
  __gwt_schedulehandled.then(function () {
    scheduleCallback = null;
  });
}

var scheduleCallback = null;
var fakeCallbackNode = {};

// Except for NoPriority, these correspond to Scheduler priorities. We use
// ascending numbers so we can compare them like numbers. They start at 90 to
// avoid clashing with Scheduler's priorities.
var ImmediatePriority = 99;
var UserBlockingPriority = 98;
var NormalPriority = 97;
var LowPriority = 96;
var IdlePriority = 95; // NoPriority is the absence of priority. Also React-only.
var NoPriority = 90;
var initialTimeMs = Date.now(); // If the scheduler yields or throws, exit the current work loop.
var currentSchedulerPriorityLevel = NormalPriority;
function frameYieldMs(renderPriority, continuation) {
  var priority = priorityLevelToFrameYieldMs(renderPriority);
  var l, c;
  return l = priority, c = continuation, {
    $$typeof: Symbol.for('react.yielding_frame'),
    priority: l,
    continuation: c
  };
}
function priorityLevelToFrameYieldMs(priority) {
  switch (priority) {
    case ImmediatePriority:
    case UserBlockingPriority:
    case NormalPriority:
      return 250;
    case LowPriority:
      return 1000;
    case IdlePriority:
    case NoPriority:
      return -1;
    default:
      return 250;
  }
}
function runWithPriority(priority, fn) {
  var previousPriority = currentSchedulerPriorityLevel;
  currentSchedulerPriorityLevel = priority;
  try {
    return fn();
  } finally {
    currentSchedulerPriorityLevel = previousPriority;
  }
}
function shouldYield() {
  return scheduleCallback !== null ? scheduleCallback.shouldYield() : false;
}

var reactPropertyMap = new Map();
var weaklyHeldMap = new WeakMap();

/**
 * Appends the react bottom sheet property to the payload.
 */
function appendInitialChild(parentInstance, child) {
  if (child.nodeType === 1) {
    var payload = weaklyHeldMap.get(parentInstance);
    if (!payload) {
      payload = new Map();
      weaklyHeldMap.set(parentInstance, payload);
    }
    var key = reactPropertyMap.get(child);
    if (key) {
      payload.set(key, child);
    } else if (child.hasAttribute('__reactbottomsheet')) {
      key = child.getAttribute('__reactbottomsheet');
      reactPropertyMap.set(child, key);
      payload.set(key, child);
    }
  }
  parentInstance.appendChild(child);
}

// -----------------------------------------------------------------------------
var REACT_ELEMENT_TYPE = Symbol.for('react.element');
var REACT_PORTAL_TYPE = Symbol.for('react.portal');
var REACT_FRAGMENT_TYPE = Symbol.for('react.fragment');
var REACT_STRICT_MODE_TYPE = Symbol.for('react.strict_mode');
var REACT_PROFILER_TYPE = Symbol.for('react.profiler');
var REACT_PROVIDER_TYPE = Symbol.for('react.provider');
var REACT_CONTEXT_TYPE = Symbol.for('react.context');
var REACT_FORWARD_REF_TYPE = Symbol.for('react.forward_ref');
var REACT_SUSPENSE_TYPE = Symbol.for('react.suspense');
var REACT_SUSPENSE_LIST_TYPE = Symbol.for('react.suspense_list');
var REACT_MEMO_TYPE = Symbol.for('react.memo');
var REACT_LAZY_TYPE = Symbol.for('react.lazy');
var REACT_SCOPE_TYPE = Symbol.for('react.scope');
var REACT_DEBUG_TRACING_MODE_TYPE = Symbol.for('react.debug_tracing_mode');
var REACT_OFFSCREEN_TYPE = Symbol.for('react.offscreen');
var REACT_LEGACY_HIDDEN_TYPE = Symbol.for('react.legacy_hidden');
var REACT_CACHE_TYPE = Symbol.for('react.cache');
var REACT_SERVER_CONTEXT_TYPE = Symbol.for('react.server_context');
var REACT_TRACING_MARKER_TYPE = Symbol.for('react.tracing_marker');
var REACT_MEMO_CACHE_SENTINEL = Symbol.for('react.memo_cache_sentinel');
var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
var FAUX_ITERATOR_SYMBOL = '@@iterator';
function getIteratorFn(maybeIterable) {
  if (maybeIterable === null || typeof maybeIterable !== 'object') {
    return null;
  }
  var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
  if (typeof maybeIterator === 'function') {
    return maybeIterator;
  }
  return null;
}
var assign = Object.assign;

// Helpers to patch console.logs to avoid logging during side-effect free
// replaying on render function. This currently only patches the object
// lazily which won't cover if the log function was extracted eagerly.
// We could also eagerly patch the method.
var disabledDepth = 0;
var prevLog;
var prevInfo;
var prevWarn;
var prevError;
var prevGroup;
var prevGroupCollapsed;
var prevGroupEnd;
function disabledLog() {}
disabledLog.__reactDisabledLog = true;
function disableLogs() {
  if (disabledDepth === 0) {
    /* eslint-disable no-console */
    prevLog = console.log;
    prevInfo = console.info;
    prevWarn = console.warn;
    prevError = console.error;
    prevGroup = console.group;
    prevGroupCollapsed = console.groupCollapsed;
    prevGroupEnd = console.groupEnd; // https://github.com/facebook/react/issues/19099
    var props = {
      configurable: true,
      enumerable: true,
      value: disabledLog,
      writable: true
    }; // $FlowFixMe Flow thinks console is immutable.
    Object.defineProperties(console, {
      info: props,
      log: props,
      warn: props,
      error: props,
      group: props,
      groupCollapsed: props,
      groupEnd: props
    });
    /* eslint-enable no-console */
  }

  disabledDepth++;
}
function reenableLogs() {
  disabledDepth--;
  if (disabledDepth === 0) {
    /* eslint-disable no-console */
    var props = {
      configurable: true,
      enumerable: true,
      writable: true
    }; // $FlowFixMe Flow thinks console is immutable.
    Object.defineProperties(console, {
      log: assign({}, props, {
        value: prevLog
      }),
      info: assign({}, props, {
        value: prevInfo
      }),
      warn: assign({}, props, {
        value: prevWarn
      }),
      error: assign({}, props, {
        value: prevError
      }),
      group: assign({}, props, {
        value: prevGroup
      }),
      groupCollapsed: assign({}, props, {
        value: prevGroupCollapsed
      }),
      groupEnd: assign({}, props, {
        value: prevGroupEnd
      })
    });
    /* eslint-enable no-console */
  }

  if (disabledDepth < 0) {
    error('disabledDepth fell below zero. This is a bug in React. Please file an issue.');
  }
}

/**
 * Forked from fbjs/warning:
 * https://github.com/facebook/fbjs/blob/e66ba20ad5be433eb54423f2b097d829324d9de6/packages/fbjs/src/warning.js
 *
 * Only uses console.error for message disclosure.
 * MIT licensed
 */
function GwtWorkarounds() {}

// In DEV, calls to this function are replaced with assertions by a Babel plugin.
// In PROD, this is a empty function.
var ReactCurrentDispatcher$1 = ReactSharedInternals.ReactCurrentDispatcher;
var prefix;
function describeBuiltInComponentFrame(name, source, ownerFn) {
  if (prefix === undefined) {
    // Extract the VM specific prefix used by each environment.
    try {
      throw Error();
    } catch (x) {
      var match = x.stack.trim().match(/\n( *(at )?)/);
      prefix = match && match[1] || '';
    }
  } // We use the prefix to ensure our stacks line up with native stack frames.
  return '\n' + prefix + name;
}
var reentry = false;
function describeNativeComponentFrame(fn, construct) {
  // If something asked for a stack inside a fake render, it should get ignored.
  if (!fn || reentry) {
    return '';
  }
  var control;
  reentry = true;
  var previousPrepareStackTrace = Error.prepareStackTrace; // $FlowFixMe It does accept undefined.
  Error.prepareStackTrace = undefined;
  var previousDispatcher;
  previousDispatcher = ReactCurrentDispatcher$1.current; // Set the dispatcher in DEV because this might be call in the render function
  // for warnings.
  ReactCurrentDispatcher$1.current = null;
  disableLogs();
  try {
    // This should throw.
    if (construct) {
      // Something should be setting the props in the constructor.
      var Fake = function () {
        throw Error();
      }; // $FlowFixMe
      Object.defineProperty(Fake.prototype, 'props', {
        set: function () {
          // We use a throwing setter instead of frozen object because with a frozen object
          // an assignment will fail silently in strict mode, and ignore the assignment in
          // loose mode. You can't observe a failed assignment reliably.
          throw Error();
        }
      });
      if (typeof Reflect === 'object' && Reflect.construct) {
        // We construct a different control for this case to include any extra
        // frames added by the construct call.
        try {
          Reflect.construct(Fake, []);
        } catch (x) {
          control = x;
        }
        Reflect.construct(fn, [], Fake);
      } else {
        try {
          Fake.call();
        } catch (x) {
          control = x;
        }
        fn.call(Fake.prototype);
      }
    } else {
      try {
        throw Error();
      } catch (x) {
        control = x;
      } // TODO(luna): This will currently only throw if the function component
      // tries to access props since we don't pass any. It won't throw if it
      // doesn't try to access props. We should probably pass a marker to
      // stand-in for the props so that we can reliably detect when we're
      // inside a fn component.
      var maybePromise = fn(); // If the function component returns a promise, it's likely an async
      // component, which we don't yet support. Attach a noop catch handler to
      // silence warnings.
      if (maybePromise && typeof maybePromise.catch === 'function') {
        maybePromise.catch(function () {});
      }
    }
  } catch (sample) {
    // This is inlined manually because closure doesn't do it for us.
    if (sample && control && typeof sample.stack === 'string') {
      // This extracts the stack from the sample throw, then removes the
      // calling frame from the stack so that it's appears to be call from
      // the fn component itself.
      return '\n' + sample.stack.slice(sample.stack.indexOf('\n', sample.stack.indexOf(control.message) + control.message.length) + 1);
    }
  } finally {
    reentry = false;
    ReactCurrentDispatcher$1.current = previousDispatcher;
    reenableLogs();
    Error.prepareStackTrace = previousPrepareStackTrace;
  } // Fallback to just returning the name of the function.
  var name = fn.displayName || fn.name;
  return name ? describeBuiltInComponentFrame(name) : '';
}
function describeClassComponentFrame(ctor, source, ownerFn) {
  return describeNativeComponentFrame(ctor, true);
}
function describeFunctionComponentFrame(fn, source, ownerFn) {
  return describeNativeComponentFrame(fn, false);
}
function getStackByComponentStackNode(componentStack) {
  try {
    var info = '';
    var node = componentStack;
    do {
      var owner = node._owner;
      var source = node._source;
      var name = node.type.displayName || node.type.name || null;
      var ownerName = owner ? owner.type.displayName || owner.type.name || null : null;
      var ownerSource = owner && owner._source;
      var frame = describeComponentFrame(node.type, source, name, owner, ownerSource, ownerName);
      info += frame;
      node = node.return;
    } while (node);
    return info;
  } catch (x) {
    return '\nError generating stack: ' + x.message + '\n' + x.stack;
  }
}
function describeComponentFrame(type, source, name, owner, ownerSource, ownerName) {
  var ownerNameCap = ownerName ? ownerName.charAt(0).toUpperCase() + ownerName.slice(1) : '';
  var sourceInfo = source ? ' (at ' + source.fileName.replace(/^.*[\\\/]/, '') + ':' + source.lineNumber + ')' : '';
  if (owner) {
    var ownerSourceInfo = ownerSource ? ' (at ' + ownerSource.fileName.replace(/^.*[\\\/]/, '') + ':' + ownerSource.lineNumber + ')' : '';
    return '\n    in ' + (name || 'Unknown') + sourceInfo + (owner ? ' (created by ' + ownerNameCap + ownerSourceInfo + ')' : '');
  }
  return '\n    in ' + (name || 'Unknown') + sourceInfo;
}

// This is a host config that's used for the `react-reconciler` package on npm.
// It is only used by third-party renderers.
//
// Its API lets you specify the host platform to rendered to. You can write
// a renderer that injects a reconciler and uses this host config to render
// to something custom. For example, it could be a test renderer.
//
//
//
// This lets us use a single host config that makes it easy to test
// the renderer both on server and on client.
var NO_CONTEXT = {};
var scheduleTimeout = typeof setTimeout === 'function' ? setTimeout : undefined;
var cancelTimeout = typeof clearTimeout === 'function' ? clearTimeout : undefined;
var noTimeout = -1; // -------------------
var supportsMutation = true;
function getPublicInstance(instance) {
  return instance;
}
function getRootHostContext(rootContainerInstance) {
  return NO_CONTEXT;
}
function getChildHostContext(parentHostContext, type, rootContainerInstance) {
  return NO_CONTEXT;
}
function prepareForCommit(containerInfo) {
  // noop
  return null;
}
function resetAfterCommit(containerInfo) {}
// noop
function createInstance(type, props, rootContainerInstance, hostContext, internalInstanceHandle) {
  // TODO: Implement this.
  return null;
}
function appendInitialChild$1(parentInstance, child) {
  // TODO: Implement this.
}
function finalizeInitialChildren(domElement, type, props, rootContainerInstance, hostContext) {
  // TODO: Implement this.
  return false;
}
function prepareUpdate(domElement, type, oldProps, newProps, rootContainerInstance, hostContext) {
  // TODO: Implement this.
  return null;
}
function shouldSetTextContent(type, props) {
  return false;
}
function shouldDeprioritizeSubtree(type, props) {
  return false;
}
function createTextInstance(text, rootContainerInstance, hostContext, internalInstanceHandle) {
  // TODO: Implement this.
  return null;
}
function scheduleDeferredCallback(callback) {
  // noop
  return null;
}
function cancelDeferredCallback(callbackID) {}
// noop
function setTimeout$1(handler, timeout) {
  return scheduleTimeout(handler, timeout);
}
function clearTimeout$1(handle) {
  cancelTimeout(handle);
}
function commitMount(domElement, type, newProps, internalInstanceHandle) {}
// noop
function commitUpdate(domElement, updatePayload, type, oldProps, newProps, internalInstanceHandle) {}
// noop
function resetTextContent(domElement) {}
// noop
function commitTextUpdate(textInstance, oldText, newText) {}
// noop
function appendChild(parentInstance, child) {}
// noop
function appendChildToContainer(container, child) {}
// noop
function insertBefore(parentInstance, child, beforeChild) {}
// noop
function insertInContainerBefore(container, child, beforeChild) {}
// noop
function removeChild(parentInstance, child) {}
// noop
function removeChildFromContainer(container, child) {}
// noop
function hideInstance(instance) {}
// noop
function hideTextInstance(textInstance) {}
// noop
function unhideInstance(instance, props) {}
// noop
function unhideTextInstance(textInstance, text) {}
// noop
function getInstanceFromNode(node) {
  return null;
}

var emptyObject = {};
var didWarnAboutMessageChannel = false;
var enqueueTask;
try {
  // read require('reason')
  enqueueTask = require('fs').readFile.bind(null, __filename, function () {});
} catch (e) {
  // read require('reason')
  enqueueTask = function (task) {
    return scheduleTimeout(task, 0);
  };
}
function findHostInstanceByFiber(fiber) {
  var hostFiber = findCurrentHostFiber(fiber);
  if (hostFiber === null) {
    return null;
  }
  return hostFiber.stateNode;
}
function emptyFindFiberByHostInstance(instance) {
  return null;
}
function getCurrentFiberForDevTools() {
  return ReactCurrentOwner.current;
}

/**
 * Coerces a string to a number, run-time checking for
 * non-finites. This is safe to use with strings that can be coerced to
 * numbers.
 */
function JsxNumberCoercion(string) {
  if (string == null || string.length === 0) {
    return NaN;
  }
  var number = Number(string);
  return isFinite(number) ? number : NaN;
}

/**
 * Similar to invariant but only logs a warning if the condition is not met.
 * This can be used to log issues in development environments in critical
 * paths. Removing the logging code for production environments will keep the
 * same logic and follow the same code paths.
 */
var ReactVersion = '19.0.0-www-classic-b049b0b18-20240612';
var HIDE_VERBOSE_LOGS = process.env.NODE_ENV === 'production' || typeof window === 'undefined' || window.document == null || typeof window.document.createElement !== 'function';

/**

 * `ReactInstanceMap` maintains a mapping from a public facing stateful
 * instance (key) to the internal representation (value). This allows public
 * methods to accept the user facing instance as an argument and map them back
 * to internal methods.
 *
 * Note that this module is currently shared and assumed to be stateless.
 * If you need to upgrade this module to be stateful, you will need to reject
 * this TEMPLATE and create a specific version of this module.
 */
var ReactIsomorphic = {
  // TODO: Figure out why this is here.
  // It's not used by anything in www.
  // Probably some test that was deleted?
  // Or maybe it's just not used by anything anymore.
  // It is used by React ART though.
  //
  //
  //
  //
  //
  // isMounted: function(instance) {
  //   var internalInstance = ReactInstanceMap.get(instance);
  //   if (!internalInstance) {
  //     return false;
  //   }
  //   return internalInstance.tag === HostComponent || internalInstance.tag === ClassComponent;
  // },
  //
  //
  // findDOMNode: function(instance) {
  //   if (instance == null) {
  //     return null;
  //   }
  //   if (instance.nodeType === 1) {
  //     return instance;
  //   }
  //   var internalInstance = ReactInstanceMap.get(instance);
  //   if (internalInstance) {
  //     return findHostInstance(internalInstance);
  //   }
  //
  //   if (typeof instance.render === 'function') {
  //     throw new Error('Unable to find node on an unmounted component.');
  //   } else {
  //     throw new Error('Element appears to be neither ReactComponent nor DOMNode. Keys: ' + Object.keys(instance));
  //   }
  // },
  //
  //
  // unmountComponentAtNode: function(container) {
  //   var root = ReactDOM.unstable_legacyFindRootForNode(container);
  //   if (root != null) {
  //     root.unmount();
  //     return true;
  //   }
  //   return false;
  // },
  //
  //
  // render: function(element, container, callback) {
  //   return legacyRenderSubtreeIntoContainer(
  //     null,
  //     element,
  //     container,
  //     false,
  //     callback
  //   );
  // },
};

/**
 * Checks if an event is supported in the current execution environment.
 *
 * NOTE: This will not work correctly for non-generic events such as `change`,
 * `reset`, `load`, `error`, and `select`.
 *
 * Borrows from Modernizr.
 *
 * @param {string} eventNameSuffix Event name, e.g. "click".
 * @return {boolean} True if the event is supported.
 * @internal
 * @license Modernizr 3.0.0pre (Custom Build) | MIT
 */
function isEventSupported(eventNameSuffix) {
  if (!ExecutionEnvironment.canUseDOM) {
    return false;
  }
  var eventName = 'on' + eventNameSuffix;
  var isSupported = eventName in document;
  if (!isSupported) {
    var element = document.createElement('div');
    element.setAttribute(eventName, 'return;');
    isSupported = typeof element[eventName] === 'function';
  }
  return isSupported;
}
var currentlyRenderingComponent = null;
var firstWorkInProgressHook = null;
var workInProgressHook = null; // Whether the work-in-progress hook is a re-rendered hook
var isReRender = false; // Whether an update was scheduled during the currently executing render pass.
var didScheduleRenderPhaseUpdate = false; // Lazily created map of render-phase updates
var renderPhaseUpdates = null; // Counter to prevent infinite loops.
var numberOfReRenders = 0;
var RE_RENDER_LIMIT = 25;
function resolveCurrentlyRenderingComponent() {
  if (currentlyRenderingComponent === null) {
    throw new Error('Invalid hook call. Hooks can only be called inside of the body of a function component. This could happen for' + ' one of the following reasons:\n' + '1. You might have mismatching versions of React and the renderer (such as React DOM)\n' + '2. You might be breaking the Rules of Hooks\n' + '3. You might have more than one copy of React in the same app\n' + 'See https://react.dev/link/invalid-hook-call for hints.');
  }
  return currentlyRenderingComponent;
}
function areHookInputsEqual(nextDeps, prevDeps) {
  if (prevDeps === null) {
    return false;
  }
  for (var i = 0; i < prevDeps.length && i < nextDeps.length; i++) {
    if (objectIs(nextDeps[i], prevDeps[i])) {
      continue;
    }
    return false;
  }
  return true;
}

/**
 * `charCode` represents the actual numeric value of the key that was pressed.
 *
 * `key` is the string value of the key that was pressed.
 *
 * `keyCode` is a numeric value that represents the key that was pressed.
 * It is often the same as `charCode` but has many inconsistencies.
 *
 * @see http://www.w3.org/TR/DOM-Level-3-Events/#events-KeyboardEvent
 */
var supportedInputTypes = {
  color: true,
  date: true,
  datetime: true,
  'datetime-local': true,
  email: true,
  month: true,
  number: true,
  password: true,
  range: true,
  search: true,
  tel: true,
  text: true,
  time: true,
  url: true,
  week: true
};
function isTextInputElement(elem) {
  var nodeName = elem && elem.nodeName && elem.nodeName.toLowerCase();
  if (nodeName === 'input') {
    return !!supportedInputTypes[elem.type];
  }
  if (nodeName === 'textarea') {
    return true;
  }
  return false;
}
function getEventKey(nativeEvent) {
  var key = nativeEvent.key;
  if (key === 'Unidentified') {
    return 'Unidentified';
  } // Some browsers, such as IE11 and Edge, use "Left", "Right", "Up", "Down"
  // instead of "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown".
  if (key === 'Left') {
    return 'ArrowLeft';
  }
  if (key === 'Right') {
    return 'ArrowRight';
  }
  if (key === 'Up') {
    return 'ArrowUp';
  }
  if (key === 'Down') {
    return 'ArrowDown';
  }
  return key;
}

/**
 * `precacheFiberNode` stores a fiber node on an instance.
 *
 * @param {DOMElement} hostInst The instance of a DOM element.
 * @param {Fiber} node The fiber node to store.
 */
function precacheFiberNode(hostInst, node) {
  node[internalInstanceKey] = hostInst;
}

/**
 * Given a DOM node, return the closest HostComponent or HostText fiber ancestor.
 * If the target node is being mounted, such that it has not yet been assigned
 * a parent, we must search up the DOM tree to find the parent fiber.
 *
 * @param {DOMNode} targetNode The DOM node to search from.
 * @return {Fiber} The closest HostComponent or HostText fiber ancestor.
 */
function getClosestInstanceFromNode(targetNode) {
  var targetInst = targetNode[internalInstanceKey];
  if (targetInst) {
    return targetInst;
  }
  if (!targetNode[internalPropsKey]) {
    // If the direct target doesn't have internal props, we might be inside a
    // portal so we search up to see if a parent has a fiber instance.
    var parentNode = targetNode.parentNode;
    while (parentNode) {
      targetInst = parentNode[internalInstanceKey];
      if (targetInst) {
        var parentInst = targetInst;
        var parentType = parentInst.tag; // Generally, we don't want to traverse past the root of a React tree.
        // However, modules like ReactDOMNeedsTouchEvents will attach GCs to the
        // body, which means we need to traverse up to the DOM root.
        if (parentType === HostComponent && parentInst.stateNode.tagName.toUpperCase() !== 'BODY') {
          return parentInst;
        }
        return null;
      }
      parentNode = parentNode.parentNode;
    }
  } // We are not inside a portal.
  return null;
}

// TODO: direct imports like some-package/src/* are bad. Fix me.
var hasOwnProperty = Object.prototype.hasOwnProperty;
var isArrayImpl = Array.isArray; // eslint-disable-next-line no-redeclare
function isArray(a) {
  return isArrayImpl(a);
}
var FunctionComponent = 0;
var ClassComponent = 1;
var IndeterminateComponent = 2; // Before we know whether it is function or class
var HostRoot = 3; // Root of a host tree. Could be nested inside another renderer.
var HostPortal = 4; // A subtree. Could be an entry point to a different renderer.
var HostComponent = 5;
var HostText = 6;
var Fragment = 7;
var Mode = 8;
var ContextConsumer = 9;
var ContextProvider = 10;
var ForwardRef = 11;
var Profiler = 12;
var SuspenseComponent = 13;
var MemoComponent = 14;
var SimpleMemoComponent = 15;
var LazyComponent = 16;
var IncompleteClassComponent = 17;
var DehydratedFragment = 18;
var SuspenseListComponent = 19;
var ScopeComponent = 21;
var OffscreenComponent = 22;
var LegacyHiddenComponent = 23;
var CacheComponent = 24;
var TracingMarkerComponent = 25;
var HostHoistable = 26;
var HostSingleton = 27;

// This is just thrown whenever we need to interrupt the event loop. It can be
// caught specifically to resume the event loop later.
var FailInReplay = new Error('Fail in replay.');
var FLUSH_BATCHED_UPDATES = 1;
var FLUSH_SYNC = 2;
var IS_REPLAYED = 4;
var RENDER_PHASE = 8;
var fakeNode = {};
function getLowestPriority() {
  return IdlePriority;
}
function getHighestPriority() {
  return ImmediatePriority;
}
function lanesToPriority(lanes) {
  switch (getHighestPriorityLane(lanes)) {
    case SyncLane:
      return ImmediatePriority;
    case SyncBatchedLane:
      return UserBlockingPriority;
    case InputDiscreteLane:
      return UserBlockingPriority;
    case DefaultLane:
      return NormalPriority;
    case TransitionLane1:
    case TransitionLane2:
    case TransitionLane3:
    case TransitionLane4:
    case TransitionLane5:
    case TransitionLane6:
    case TransitionLane7:
    case TransitionLane8:
    case TransitionLane9:
    case TransitionLane10:
    case TransitionLane11:
    case TransitionLane12:
    case TransitionLane13:
    case TransitionLane14:
    case TransitionLane15:
    case RetryLane1:
    case RetryLane2:
    case RetryLane3:
    case RetryLane4:
    case RetryLane5:
      return NormalPriority;
    case IdleLane:
      return IdlePriority;
    default:
      return NoPriority;
  }
}

/**
 * Use to restore the stack after a throw.
 */
var ReactCurrentOwner$1 = ReactSharedInternals.ReactCurrentOwner;
function captureCommitHook() {}
var ReactCurrentActQueue = ReactSharedInternals.ReactCurrentActQueue;
var isLegacyActEnvironment = ReactCurrentActQueue.isBatchingLegacy;
var actScopeDepth = 0;
function isActing() {
  return IsSomeRendererActing.current || actScopeDepth > 0;
}
function getActingScope() {
  if (isLegacyActEnvironment) {
    if (ReactCurrentActQueue.current !== null) {
      return ReactCurrentActQueue.current;
    }
  }
  return null;
}
var DefaultSuspenseCallback = function (res) {
  // To be implemented.
};

var BEFORE_SLASH_RE = /^(.*)[\\\/]/;
function getComponentNameFromType(type) {
  if (type == null) {
    // Host root, text node or just invalid type.
    return null;
  }
  if (typeof type === 'function') {
    return type.displayName || type.name || null;
  }
  if (typeof type === 'string') {
    return type;
  }
  switch (type) {
    case REACT_FRAGMENT_TYPE:
      return 'Fragment';
    case REACT_PORTAL_TYPE:
      return 'Portal';
    case REACT_PROFILER_TYPE:
      return 'Profiler';
    case REACT_STRICT_MODE_TYPE:
      return 'StrictMode';
    case REACT_SUSPENSE_TYPE:
      return 'Suspense';
    case REACT_SUSPENSE_LIST_TYPE:
      return 'SuspenseList';
    case REACT_CACHE_TYPE:
      return 'Cache';
    case REACT_TRACING_MARKER_TYPE:
      return 'TracingMarker';
  }
  if (typeof type === 'object') {
    switch (type.$$typeof) {
      case REACT_CONTEXT_TYPE:
        var context = type;
        return getContextName(context) + '.Consumer';
      case REACT_PROVIDER_TYPE:
        var provider = type;
        return getContextName(provider._context) + '.Provider';
      case REACT_FORWARD_REF_TYPE:
        return getWrappedName(type, type.render, 'ForwardRef');
      case REACT_MEMO_TYPE:
        var outerName = type.displayName || null;
        if (outerName !== null) {
          return outerName;
        }
        return getComponentNameFromType(type.type) || 'Memo';
      case REACT_LAZY_TYPE:
        {
          var lazyComponent = type;
          var payload = lazyComponent._payload;
          var init = lazyComponent._init;
          try {
            return getComponentNameFromType(init(payload));
          } catch (x) {
            return null;
          }
        }
      case REACT_SERVER_CONTEXT_TYPE:
        var context$1 = type;
        return (context$1.displayName || 'ServerContext') + '.Provider';
    }
  }
  return null;
}
function getContextName(context) {
  return context.displayName || 'Context';
} // Note: There is no priority levels. Instead lanes are used related to updates.

var hasOwnProperty$1 = Object.prototype.hasOwnProperty;
var RESERVED_PROPS = {
  key: true,
  ref: true,
  __self: true,
  __source: true
};
var specialPropKeyWarningShown;
var specialPropRefWarningShown;
var didWarnAboutStringRefs;
didWarnAboutStringRefs = {};
function hasValidRef(config) {
  if (hasOwnProperty$1.call(config, 'ref')) {
    var ref = config.ref;
    if (ref !== null && typeof ref !== 'function' && typeof ref !== 'object') {
      if (config._owner) {
        var owner = config._owner;
        var componentName = getComponentNameFromType(owner.type);
        if (!didWarnAboutStringRefs[componentName]) {
          error('Element ref was specified as a string (%s) but refs must be objects with a `current` property. Did you mean to use a ref callback instead?%s', ref, getStackByComponentStackNode(owner));
          didWarnAboutStringRefs[componentName] = true;
        }
      }
      return false;
    }
  }
  return true;
}
function hasValidKey(config) {
  if (hasOwnProperty$1.call(config, 'key')) {
    var key = config.key;
    if (key !== key) {
      // NaN
      error('`key` is not a valid key! Not a number.');
    }
  }
  return config.key !== undefined;
}

/**
 * Factory method to create a new React element. This no longer adheres to
 * the class pattern, so do not use new to call it. Also, instanceof check
 * will not work. Instead test $$typeof field against Symbol.for('react.element') to check
 * if something is a React Element.
 *
 * @param {*} type
 * @param {*} props
 * @param {*} key
 * @param {string|object} ref
 * @param {*} owner
 * @param {*} self A *temporary* helper to detect places where `this` is
 * different from the `owner` when React.createElement is called, so that we
 * can warn. We want to get rid of owner and replace it with self.
 * @param {object} source An annotation object (added by a transpiler).
 * @internal
 */
var ReactElement = function (type, key, ref, self, source, owner, props) {
  var element = {
    // This tag allows us to uniquely identify this as a React Element
    $$typeof: REACT_ELEMENT_TYPE,
    // Built-in properties that belong on the element
    type: type,
    key: key,
    ref: ref,
    props: props,
    // Record the component responsible for creating this element.
    _owner: owner
  };
  element._store = {};
  Object.defineProperty(element._store, 'validated', {
    configurable: false,
    enumerable: false,
    writable: true,
    value: false
  });
  Object.defineProperty(element, '_self', {
    configurable: false,
    enumerable: false,
    writable: false,
    value: self
  });
  Object.defineProperty(element, '_source', {
    configurable: false,
    enumerable: false,
    writable: false,
    value: source
  });
  if (Object.freeze) {
    Object.freeze(element.props);
    Object.freeze(element);
  }
  return element;
};

/**
 * https://github.com/reactjs/rfcs/pull/107
 * @param {*} type
 * @param {object} props
 * @param {string} key
 */
function jsx(type, config, maybeKey) {
  var propName;
  var props = {};
  var key = null;
  var ref = null;
  if (maybeKey !== undefined) {
    key = '' + maybeKey;
  }
  if (hasValidKey(config)) {
    key = '' + config.key;
  }
  if (hasValidRef(config)) {
    ref = config.ref;
  } // Remaining properties are added to props.
  for (propName in config) {
    if (hasOwnProperty$1.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
      props[propName] = config[propName];
    }
  } // Resolve default props
  if (type && type.defaultProps) {
    var defaultProps = type.defaultProps;
    for (propName in defaultProps) {
      if (props[propName] === undefined) {
        props[propName] = defaultProps[propName];
      }
    }
  }
  return ReactElement(type, key, ref, undefined, undefined, ReactCurrentOwner.current, props);
}

/**
 * https://github.com/reactjs/rfcs/pull/107
 * @param {*} type
 * @param {object} props
 * @param {string} key
 */
function jsxDEV(type, config, maybeKey, source, self) {
  var propName;
  var props = {};
  var key = null;
  var ref = null;
  if (maybeKey !== undefined) {
    key = '' + maybeKey;
  }
  if (hasValidKey(config)) {
    key = '' + config.key;
  }
  if (hasValidRef(config)) {
    ref = config.ref;
  } // Remaining properties are added to props.
  for (propName in config) {
    if (hasOwnProperty$1.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
      props[propName] = config[propName];
    }
  } // Resolve default props
  if (type && type.defaultProps) {
    var defaultProps = type.defaultProps;
    for (propName in defaultProps) {
      if (props[propName] === undefined) {
        props[propName] = defaultProps[propName];
      }
    }
  }
  if (key || ref) {
    var displayName = typeof type === 'function' ? type.displayName || type.name || 'Unknown' : type;
    if (key) {
      defineKeyPropWarningGetter(props, displayName);
    }
    if (ref) {
      defineRefPropWarningGetter(props, displayName);
    }
  }
  return ReactElement(type, key, ref, self, source, ReactCurrentOwner.current, props);
}
function defineKeyPropWarningGetter(props, displayName) {
  var warnAboutAccessingKey = function () {
    if (!specialPropKeyWarningShown) {
      specialPropKeyWarningShown = true;
      error('%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)', displayName);
    }
  };
  warnAboutAccessingKey.isReactWarning = true;
  Object.defineProperty(props, 'key', {
    get: warnAboutAccessingKey,
    configurable: true
  });
}
function defineRefPropWarningGetter(props, displayName) {
  var warnAboutAccessingRef = function () {
    if (!specialPropRefWarningShown) {
      specialPropRefWarningShown = true;
      error('%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)', displayName);
    }
  };
  warnAboutAccessingRef.isReactWarning = true;
  Object.defineProperty(props, 'ref', {
    get: warnAboutAccessingRef,
    configurable: true
  });
}

// TODO: Need to come up with something better than this.
var IsThisRendererActing = {
  current: false
};
var ReactSharedInternals$1 = {
  ReactCurrentDispatcher: ReactCurrentDispatcher,
  ReactCurrentOwner: ReactCurrentOwner,
  ReactCurrentBatchConfig: ReactCurrentBatchConfig,
  IsSomeRendererActing: IsSomeRendererActing,
  // Used by renderers to avoid bundling object-assign twice in UMD bundles:
  assign: assign
};
ReactSharedInternals$1.ReactDebugCurrentFrame = ReactDebugCurrentFrame;

/**
 * Create a new context object. The object only has two fields:
 *
 *  - Provider: A React component that allows consuming components to subscribe
 *    to context changes.
 *  - Consumer: A React component that subscribes to context changes.
 *
 * @version
 * @see
 * @public
 */
var ContextRegistry = {};
function getComponentNameFromType$1(type) {
  if (type == null) {
    // Host root, text node or just invalid type.
    return null;
  }
  if (typeof type === 'function') {
    return type.displayName || type.name || null;
  }
  if (typeof type === 'string') {
    return type;
  }
  switch (type) {
    case REACT_FRAGMENT_TYPE:
      return 'Fragment';
    case REACT_PORTAL_TYPE:
      return 'Portal';
    case REACT_PROFILER_TYPE:
      return 'Profiler';
    case REACT_STRICT_MODE_TYPE:
      return 'StrictMode';
    case REACT_SUSPENSE_TYPE:
      return 'Suspense';
    case REACT_SUSPENSE_LIST_TYPE:
      return 'SuspenseList';
    case REACT_CACHE_TYPE:
      return 'Cache';
  }
  if (typeof type === 'object') {
    switch (type.$$typeof) {
      case REACT_CONTEXT_TYPE:
        var context = type;
        return (context.displayName || 'Context') + '.Consumer';
      case REACT_PROVIDER_TYPE:
        var provider = type;
        return (provider._context.displayName || 'Context') + '.Provider';
      case REACT_FORWARD_REF_TYPE:
        return getWrappedName$1(type, type.render, 'ForwardRef');
      case REACT_MEMO_TYPE:
        return getComponentNameFromType$1(type.type);
      case REACT_LAZY_TYPE:
        {
          var lazyComponent = type;
          var payload = lazyComponent._payload;
          var init = lazyComponent._init;
          try {
            return getComponentNameFromType$1(init(payload));
          } catch (x) {
            return null;
          }
        }
    }
  }
  return null;
}
function getWrappedName$1(outerType, innerType, wrapperName) {
  var functionName = innerType.displayName || innerType.name || '';
  return outerType.displayName || (functionName !== '' ? wrapperName + "(" + functionName + ")" : wrapperName);
}
var Children = {
  map: mapChildren,
  forEach: forEachChildren,
  count: countChildren,
  toArray: toArray,
  only: onlyChild
};
var err = runWithPriority;
var requestTransition = React.startTransition;
var LowPriority$1 = LowPriority;
var ReactVersion$1 = ReactVersion;
var StrictMode = REACT_STRICT_MODE_TYPE;
var Suspense = REACT_SUSPENSE_TYPE;
var data = {
  isMounted: false,
  enqueueForceUpdate: function () {},
  enqueueReplaceState: function () {},
  enqueueSetState: function () {}
};
var emptyRefsObject = new React.Component().refs;
var didWarnAboutStateAssignmentForComponent;
var didWarnAboutUninitializedState;
var didWarnAboutGetSnapshotBeforeUpdateWithoutDidUpdate;
var didWarnAboutLegacyLifecyclesAndDerivedState;
var didWarnAboutUndefinedDerivedState;
var warnOnUndefinedDerivedState;
var warnOnInvalidCallback;
didWarnAboutStateAssignmentForComponent = new Set();
didWarnAboutUninitializedState = new Set();
didWarnAboutGetSnapshotBeforeUpdateWithoutDidUpdate = new Set();
didWarnAboutLegacyLifecyclesAndDerivedState = new Set();
didWarnAboutUndefinedDerivedState = new Set();
var didWarnOnInvalidCallback = new Set();
warnOnInvalidCallback = function (component, callback) {
  if (callback === undefined || callback === null) {
    return;
  }
  if (typeof callback !== 'function') {
    var componentName = getComponentNameFromType$1(component.type) || 'Component';
    if (!didWarnOnInvalidCallback.has(componentName)) {
      didWarnOnInvalidCallback.add(componentName);
      error('%s.setState(...): Expected the last optional `callback` argument to be a function. Instead received: %s.', componentName, callback);
    }
  }
};
warnOnUndefinedDerivedState = function (type, partialState) {
  if (partialState === undefined) {
    var componentName = getComponentNameFromType$1(type) || 'Component';
    if (!didWarnAboutUndefinedDerivedState.has(componentName)) {
      didWarnAboutUndefinedDerivedState.add(componentName);
      error('%s.getDerivedStateFromProps(): A valid state object (or null) must be returned. You have returned undefined.', componentName);
    }
  }
};
function adoptClassInstance(workInProgress, instance) {
  instance.updater = data;
  workInProgress.stateNode = instance;
  instance._reactInternals = workInProgress;
}
function constructClassInstance(workInProgress, ctor, props) {
  var isLegacyContextConsumer = false;
  var unmaskedContext = emptyObject;
  var context = emptyObject;
  var contextType = ctor.contextType;
  if (typeof contextType === 'object' && contextType !== null) {
    context = readContext(contextType);
  } else {
    unmaskedContext = getUnmaskedContext(workInProgress, ctor, true);
    var contextTypes = ctor.contextTypes;
    isLegacyContextConsumer = contextTypes !== null && contextTypes !== undefined;
    context = isLegacyContextConsumer ? getMaskedContext(workInProgress, unmaskedContext) : emptyObject;
  }
  var instance = new ctor(props, context);
  var state = workInProgress.memoizedState = instance.state !== null && instance.state !== undefined ? instance.state : null;
  adoptClassInstance(workInProgress, instance);
  if (isLegacyContextConsumer) {
    cacheContext(workInProgress, unmaskedContext, context);
  }
  return instance;
}
function callComponentWillMount(workInProgress, instance) {
  var oldState = instance.state;
  if (typeof instance.componentWillMount === 'function') {
    instance.componentWillMount();
  }
  if (typeof instance.UNSAFE_componentWillMount === 'function') {
    instance.UNSAFE_componentWillMount();
  }
  if (oldState !== instance.state) {
    data.enqueueReplaceState(instance, instance.state, null);
  }
}
function callComponentWillReceiveProps(workInProgress, instance, newProps, nextContext) {
  var oldState = instance.state;
  if (typeof instance.componentWillReceiveProps === 'function') {
    instance.componentWillReceiveProps(newProps, nextContext);
  }
  if (typeof instance.UNSAFE_componentWillReceiveProps === 'function') {
    instance.UNSAFE_componentWillReceiveProps(newProps, nextContext);
  }
  if (instance.state !== oldState) {
    data.enqueueReplaceState(instance, instance.state, null);
  }
}
function Component(props, context, updater) {
  this.props = props;
  this.context = context; // If a component has string refs, we will assign a different object later.
  this.refs = emptyRefsObject; // We initialize the default updater but the real one gets injected by the
  // renderer.
  this.updater = updater || data;
}
Component.prototype.isReactComponent = {};
Component.prototype.setState = function (partialState, callback) {
  if (typeof partialState !== 'object' && typeof partialState !== 'function' && partialState != null) {
    throw new Error('setState(...): takes an object of state variables to update or a function which returns an object of state variables.');
  }
  this.updater.enqueueSetState(this, partialState, callback, 'setState');
};
Component.prototype.forceUpdate = function (callback) {
  this.updater.enqueueForceUpdate(this, callback, 'forceUpdate');
};
function checkShouldComponentUpdate(workInProgress, ctor, oldProps, newProps, oldState, newState, nextContext) {
  var instance = workInProgress.stateNode;
  if (typeof instance.shouldComponentUpdate === 'function') {
    var shouldUpdate = instance.shouldComponentUpdate(newProps, newState, nextContext);
    return shouldUpdate;
  }
  if (ctor.prototype && ctor.prototype.isPureReactComponent) {
    return !shallowEqual(oldProps, newProps) || !shallowEqual(oldState, newState);
  }
  return true;
}
var fakeCallback = function (arg) {
  return arg;
};
function applyDerivedStateFromProps(workInProgress, ctor, getDerivedStateFromProps, nextProps) {
  var prevState = workInProgress.memoizedState;
  var partialState = getDerivedStateFromProps(nextProps, prevState);
  warnOnUndefinedDerivedState(ctor, partialState); // Merge the partial state and the previous state.
  var memoizedState = partialState === null || partialState === undefined ? prevState : assign({}, prevState, partialState);
  workInProgress.memoizedState = memoizedState; // Once the update queue is empty, persist the derived state onto the
  // base state.
  if (workInProgress.lanes === NoLanes) {
    // Queue is empty. We should reset the cache of derived updates.
    workInProgress.updateQueue.baseState = memoizedState;
  }
}
var classComponentUpdater = {
  isMounted: isMounted,
  enqueueSetState: function (inst, payload, callback) {
    var fiber = get(inst);
    var eventTime = requestUpdateLane(fiber);
    var lane = SyncLane;
    var update = createUpdate(eventTime, lane);
    update.payload = payload;
    if (callback !== undefined && callback !== null) {
      warnOnInvalidCallback(fiber, callback);
      update.callback = callback;
    }
    var root = enqueueUpdate(fiber, update, lane);
    if (root !== null) {
      scheduleUpdateOnFiber(root, fiber, lane, eventTime);
      entangleTransitions(root, fiber, lane);
    }
  },
  enqueueReplaceState: function (inst, payload, callback) {
    var fiber = get(inst);
    var eventTime = requestUpdateLane(fiber);
    var lane = SyncLane;
    var update = createUpdate(eventTime, lane);
    update.tag = ReplaceState;
    update.payload = payload;
    if (callback !== undefined && callback !== null) {
      warnOnInvalidCallback(fiber, callback);
      update.callback = callback;
    }
    var root = enqueueUpdate(fiber, update, lane);
    if (root !== null) {
      scheduleUpdateOnFiber(root, fiber, lane, eventTime);
      entangleTransitions(root, fiber, lane);
    }
  },
  enqueueForceUpdate: function (inst, callback) {
    var fiber = get(inst);
    var eventTime = requestUpdateLane(fiber);
    var lane = SyncLane;
    var update = createUpdate(eventTime, lane);
    update.tag = ForceUpdate;
    if (callback !== undefined && callback !== null) {
      warnOnInvalidCallback(fiber, callback);
      update.callback = callback;
    }
    var root = enqueueUpdate(fiber, update, lane);
    if (root !== null) {
      scheduleUpdateOnFiber(root, fiber, lane, eventTime);
      entangleTransitions(root, fiber, lane);
    }
  }
};
var PureComponent = /*#__PURE__*/function (_Component) {
  _inheritsLoose(PureComponent, _Component);
  function PureComponent() {
    return _Component.apply(this, arguments) || this;
  }
  var _proto = PureComponent.prototype;
  _proto.isPureReactComponent = true;
  return PureComponent;
}(Component);
var previousUsedContextDev = new Set();
var currentHook = null;
var nextHook = null;
var firstHook = null;
var isReRender$1 = false;
var didScheduleRenderPhaseUpdate$1 = false;
var renderPhaseUpdates$1 = null;
var numberOfReRenders$1 = 0;
function areHookInputsEqual$1(nextDeps, prevDeps) {
  if (prevDeps === null) {
    return false;
  }
  for (var i = 0; i < prevDeps.length && i < nextDeps.length; i++) {
    if (objectIs(nextDeps[i], prevDeps[i])) {
      continue;
    }
    return false;
  }
  return true;
}
var currentUpdate = null;
var isUpdatingOpaqueValueInRenderPhase = false;
function getIsUpdatingOpaqueValueInRenderPhase() {
  return isUpdatingOpaqueValueInRenderPhase;
}
function currentlyRenderingFiber$1() {
  if (currentlyRenderingFiber === null) {
    throw new Error('Invalid hook call. Hooks can only be called inside of the body of a function component.');
  }
  return currentlyRenderingFiber;
}
var HooksDispatcher = {
  readContext: readContext,
  useCallback: useCallback,
  useContext: useContext,
  useEffect: useEffect,
  useImperativeHandle: useImperativeHandle,
  useLayoutEffect: useLayoutEffect,
  useMemo: useMemo,
  useReducer: useReducer,
  useRef: useRef,
  useState: useState,
  useDebugValue: useDebugValue,
  useDeferredValue: useDeferredValue,
  useTransition: useTransition,
  useOpaqueIdentifier: useOpaqueIdentifier,
  useMutableSource: useMutableSource,
  useSyncExternalStore: useSyncExternalStore,
  useId: useId,
  unstable_isNewReconciler: true
};
var HooksDispatcherOnMount = {
  readContext: readContext,
  useCallback: function (callback, deps) {
    return callback;
  },
  useContext: useContext,
  useEffect: useEffect,
  useImperativeHandle: useImperativeHandle,
  useLayoutEffect: useLayoutEffect,
  useMemo: function (nextCreate, deps) {
    return nextCreate();
  },
  useReducer: useReducer,
  useRef: useRef,
  useState: useState,
  useDebugValue: useDebugValue,
  useDeferredValue: useDeferredValue,
  useTransition: useTransition,
  useOpaqueIdentifier: useOpaqueIdentifier,
  useMutableSource: useMutableSource,
  useSyncExternalStore: useSyncExternalStore,
  useId: useId,
  unstable_isNewReconciler: true
};
function createPortal(children, containerInfo, // TODO: figure out the API for cross-renderer implementation.
implementation) {
  var key = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : null;
  return {
    // This tag allow us to uniquely identify this as a React Portal
    $$typeof: REACT_PORTAL_TYPE,
    key: key == null ? null : '' + key,
    children: children,
    containerInfo: containerInfo,
    implementation: implementation
  };
}
var REACT_CLIENT_REFERENCE$1 = Symbol.for('react.client.reference');
function getOwner() {
  var owner = ReactCurrentOwner.current;
  return owner;
}

// Corresponds to ReactFiberHostConfig.
var valueStack = [];
var fiberStack = [];
function getFiberCurrentPropsFromNode(node) {
  return node[internalPropsKey] || null;
}
function updateFiberProps(node, props) {
  node[internalPropsKey] = props;
}
var NoLane = /*                          */0;
var SyncLane = /*                        */1;
function requestCurrentTransition() {
  return ReactCurrentBatchConfig.transition;
}
var ReactCurrentActQueue$1 = ReactSharedInternals.ReactCurrentActQueue;
var DefaultSuspenseCallback$1 = function (res) {
  // To be implemented.
};

// This is the unfortunate story of how we ended up with this mess.
// We are planning to refactor this in the future.
//
// React provides a hook that will be called by the reconciler.
// It is used to patch the renderer and perform some operations.
// It's not a real public API but it's used by test renderers and devtools.
//
// In www, we use a different approach. We monkey-patch the reconciler
// methods to achieve the same result. This is largely because we want to be
// able to use different reconcilers depending on the task.
// For example, we have a reconciler for the server and a reconciler for the
// client. We also have a reconciler for testing.
//
// The problem is that the devtools need to be able to inspect the fiber tree.
// This means that they need to be able to get a hold of the reconciler.
// The way they do this is by looking at the `__REACT_DEVTOOLS_GLOBAL_HOOK__`
// global variable. This variable is set by the devtools extension.
//
// The devtools extension then uses this hook to patch the reconciler.
//
// The problem is that we have multiple reconcilers. We need to be able to
// tell the devtools which reconciler to use.
//
// We do this by having a global variable that stores the current reconciler.
// This is not ideal, but it's the best we can do for now.
//
// The other problem is that the devtools need to be able to inspect the
// fiber tree even when the reconciler is not running.
// This means that they need to be able to get a hold of the fiber tree
// even when there is no current owner.
//
// We do this by having a global variable that stores the current fiber.
// This is not ideal, but it's the best we can do for now.
//
// The other problem is that the devtools need to be able to inspect the
// fiber tree even when the reconciler is not running.
// This means that they need to be able to get a hold of the fiber tree
// even when there is no current owner.
//
// We do this by having a global variable that stores the current fiber.
// This is not ideal, but it's the best we can do for now.
var ReactFiberInstrumentation = {
  debugTool: null
};
var ReactDebugCurrentFrame$1 = ReactSharedInternals.ReactDebugCurrentFrame;
var current = null;
var isRendering = false;
var AbstractComponent = function (props, context) {
  // This is a abstract component that should not be used directly.
};
AbstractComponent.prototype.isReactComponent = {};
AbstractComponent.prototype.setState = function (partialState, callback) {
  this.updater.enqueueSetState(this, partialState, callback, 'setState');
};
AbstractComponent.prototype.forceUpdate = function (callback) {
  this.updater.enqueueForceUpdate(this, callback, 'forceUpdate');
};
var ReactVersion$2 = '19.0.0-www-classic-b049b0b18-20240612';

// -----------------------------------------------------------------------------
var ReactPropTypesSecret$1 = 'SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED';
var ReactPropTypesSecret_1 = ReactPropTypesSecret$1;
var ReactPropTypesSecret = ReactPropTypesSecret_1;
var has = Function.call.bind(Object.prototype.hasOwnProperty);
var printWarning = function () {};
printWarning = function (text) {
  var message = 'Warning: ' + text;
  if (typeof console !== 'undefined') {
    console.error(message);
  }
  try {
    // --- Welcome to debugging React ---
    // This error was thrown as a convenience so that you can use this stack
    // to find the callsite that caused this warning to fire.
    throw new Error(message);
  } catch (x) {}
};
function checkPropTypes(typeSpecs, values, location, componentName, getStack) {
  for (var typeSpecName in typeSpecs) {
    if (has(typeSpecs, typeSpecName)) {
      var error$1;
      // Prop type validation may throw. In case they do, we want to catch
      // the error and provide a better error message.
      try {
        // This is intentionally an invariant that gets caught. It's the same
        // behavior as without this statement except with a better message.
        if (typeof typeSpecs[typeSpecName] !== 'function') {
          var err = Error((componentName || 'React class') + ': ' + location + ' type `' + typeSpecName + '` is invalid; ' + 'it must be a function, usually from the `prop-types` package, but received `' + typeof typeSpecs[typeSpecName] + '`.' + 'This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`.');
          err.name = 'Invariant Violation';
          throw err;
        }
        error$1 = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, ReactPropTypesSecret);
      } catch (ex) {
        error$1 = ex;
      }
      if (error$1 && !(error$1 instanceof Error)) {
        printWarning((componentName || 'React class') + ': type specification of ' + location + ' `' + typeSpecName + '` is invalid; the type checker ' + 'function must return `null` or an `Error` but returned a ' + typeof error$1 + '. ' + 'You may have forgotten to pass an argument to the type checker ' + 'creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, shape).');
      }
      if (error$1 instanceof Error && !(error$1.message in loggedTypeFailures)) {
        // Only monitor this failure once because there tends to be a lot of the
        // same error.
        loggedTypeFailures[error$1.message] = true;
        var stack = getStack ? getStack() : '';
        printWarning('Failed ' + location + ' type: ' + error$1.message + (stack != null ? stack : ''));
      }
    }
  }
}
var BEFORE_SLASH_RE$1 = /^(.*)[\\\/]/;
var getComponentNameFromType$2 = getComponentNameFromType;
var getStack = function () {
  var owner = ReactDebugCurrentFrame$1.getCurrentStack();
  if (owner) {
    return getStackByFiberInDevAndProd(owner);
  }
  return '';
};
var VALID_FRAGMENT_PROPS = new Map([['key', true], ['children', true]]);
var didWarnAboutMaps;
var didWarnAboutGenerators;
var didWarnAboutStringRefs$1;
var ownerHasKeyUseWarning;
var ownerHasFunctionUseWarning;
var warnForMissingKey = function (child, returnFiber) {};
didWarnAboutMaps = false;
didWarnAboutGenerators = false;
didWarnAboutStringRefs$1 = {};
ownerHasKeyUseWarning = {};
ownerHasFunctionUseWarning = {};
var validateExplicitKey = function (element, parentType) {
  if (!element._store || element._store.validated) {
    return;
  }
  element._store.validated = true;
  var currentComponentErrorInfo = ' See ' + getStack();
  if (ownerHasKeyUseWarning[parentType] || ownerHasFunctionUseWarning[parentType]) {
    return;
  }
  if (element.key !== null && element.key !== undefined) {
    return;
  }
  if (typeof element.type === 'object' && element.type !== null && element.type.$$typeof === REACT_FRAGMENT_TYPE) {
    for (var prop in element.props) {
      if (hasOwnProperty.call(element.props, prop) && !VALID_FRAGMENT_PROPS.has(prop)) {
        ownerHasKeyUseWarning[parentType] = true;
        error('Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.%s', prop, currentComponentErrorInfo);
        break;
      }
    }
  }
};
var createElement = ReactElement;
var cloneElement = function (element, config, children) {
  if (element === null || element === undefined) {
    throw new Error("React.cloneElement(...): The argument must be a React element, but you passed " + element + ".");
  }
  var propName; // Original props are copied
  var props = assign({}, element.props); // Reserved names are extracted
  var key = element.key;
  var ref = element.ref; // Self is preserved since the owner is preserved.
  var self = element._self; // Source is preserved since cloneElement is unlikely to be targeted by a
  // transpiler, and even if it is, the original source is more valuable.
  var source = element._source; // Owner will be preserved, unless ref is overridden
  var owner = element._owner;
  if (config != null) {
    if (hasValidRef(config)) {
      // Silently steal the ref from the parent instance.
      ref = config.ref;
      owner = ReactCurrentOwner.current;
    }
    if (hasValidKey(config)) {
      key = '' + config.key;
    } // Remaining properties override existing props
    var defaultProps;
    if (element.type && element.type.defaultProps) {
      defaultProps = element.type.defaultProps;
    }
    for (propName in config) {
      if (hasOwnProperty$1.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
        if (config[propName] === undefined && defaultProps !== undefined) {
          // Resolve default props
          props[propName] = defaultProps[propName];
        } else {
          props[propName] = config[propName];
        }
      }
    }
  } // Children can be more than one argument, and those are transferred onto
  // the newly allocated props object.
  var childrenLength = arguments.length - 2;
  if (childrenLength === 1) {
    props.children = children;
  } else if (childrenLength > 1) {
    var childArray = Array(childrenLength);
    for (var i = 0; i < childrenLength; i++) {
      childArray[i] = arguments[i + 2];
    }
    props.children = childArray;
  }
  return ReactElement(element.type, key, ref, self, source, owner, props);
};
var createFactory = function (type) {
  var factory = createElement.bind(null, type);
  factory.type = type;
  return factory;
};
function lazy(ctor) {
  var payload = {
    // We use these fields to store the result.
    _status: -1,
    _result: ctor
  };
  var lazyType = {
    $$typeof: REACT_LAZY_TYPE,
    _payload: payload,
    _init: lazyInitializer
  };
  return lazyType;
}
function forwardRef(render) {
  if (render != null && render.$$typeof === REACT_MEMO_TYPE) {
    error('forwardRef requires a render function but received a `memo` component. Instead of forwardRef(memo(...)), use memo(forwardRef(...)).');
  } else if (typeof render !== 'function') {
    error('forwardRef requires a render function but was given %s.', render === null ? 'null' : typeof render);
  } else {
    if (render.length !== 0 && render.length !== 2) {
      error('forwardRef render functions accept exactly two parameters: props and ref. %s', render.length === 1 ? 'Did you forget to use the ref parameter?' : 'Any additional parameter will be undefined.');
    }
  }
  if (render != null) {
    if (render.defaultProps != null || render.propTypes != null) {
      error('forwardRef render functions do not support defaultProps or propTypes.');
    }
  }
  var elementType = {
    $$typeof: REACT_FORWARD_REF_TYPE,
    render: render
  };
  Object.defineProperty(elementType, 'displayName', {
    enumerable: false,
    configurable: true,
    get: function () {
      return getWrappedName$1(elementType, render, 'ForwardRef');
    }
  });
  return elementType;
}
function isValidElement(object) {
  return typeof object === 'object' && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
}
function memo(type, compare) {
  if (typeof type !== 'function') {
    error('memo: The first argument must be a component. Instead received: %s', type === null ? 'null' : typeof type);
  }
  var elementType = {
    $$typeof: REACT_MEMO_TYPE,
    type: type,
    compare: compare === undefined ? null : compare
  };
  Object.defineProperty(elementType, 'displayName', {
    enumerable: false,
    configurable: true,
    get: function () {
      return getComponentNameFromType(type);
    }
  });
  return elementType;
}
function cache(fn) {
  return fn;
}
var useSyncExternalStore$1 = useSyncExternalStore;
function use(usable) {
  var dispatcher = ReactCurrentDispatcher.current;
  if (dispatcher !== null) {
    return dispatcher.use(usable);
  } else {
    // Outside a component, we can't use a hook. We use the
    // old behavior of throwing a promise.
    if (isThenable(usable)) {
      // This is a promise.
      throw usable;
    }
    return usable.value;
  }
}
function startTransition(scope, options) {
  var prevTransition = ReactCurrentBatchConfig.transition;
  ReactCurrentBatchConfig.transition = {};
  try {
    scope();
  } finally {
    ReactCurrentBatchConfig.transition = prevTransition;
  }
}
function unstable_act(callback) {
  var actingScope = getActingScope();
  if (actingScope !== null) {
    // If we're already inside an `act` scope, this is a no-op.
    return callback();
  } else {
    var previousIsSomeRendererActing = IsSomeRendererActing.current;
    var prevIsLegacyActEnvironment = isLegacyActEnvironment;
    IsSomeRendererActing.current = true;
    isLegacyActEnvironment = true;
    try {
      // Replicate behavior of original `act` implementation in legacy renderers.
      var result = runWithPriority(ImmediatePriority, function () {
        return callback();
      });
      return result;
    } finally {
      IsSomeRendererActing.current = previousIsSomeRendererActing;
      isLegacyActEnvironment = prevIsLegacyActEnvironment;
    }
  }
}
function createContext(defaultValue) {
  var context = {
    $$typeof: REACT_CONTEXT_TYPE,
    // As a workaround to support multiple concurrent renderers, we categorize
    // some renderers as primary and others as secondary. We only expect
    // there to be two concurrent renderers at most: React Native (primary) and
    // Fabric (secondary); React DOM (primary) and React ART (secondary).
    // Secondary renderers store their context values on separate fields.
    _currentValue: defaultValue,
    _currentValue2: defaultValue,
    // Used to track how many concurrent renderers this context currently
    // supports within in a single renderer. Such as parallel server rendering.
    _threadCount: 0,
    // These are circular
    Provider: null,
    Consumer: null,
    // Add these to use same hidden class in VM as ServerContext
    _defaultValue: null,
    _globalName: null
  };
  context.Provider = {
    $$typeof: REACT_PROVIDER_TYPE,
    _context: context
  };
  var consumer = {
    $$typeof: REACT_CONTEXT_TYPE,
    _context: context
  }; // For backwards compatibility, the consumer property points to the context object itself.
  context.Consumer = consumer;
  context._currentRenderer = null;
  context._currentRenderer2 = null;
  return context;
}
var Children$1 = Children;
var err$1 = err;
var Component$1 = Component;
var Fragment = REACT_FRAGMENT_TYPE;
var Profiler$1 = REACT_PROFILER_TYPE;
var PureComponent$1 = PureComponent;
var StrictMode$1 = StrictMode;
var Suspense$1 = Suspense;
var SuspenseList = REACT_SUSPENSE_LIST_TYPE;
var act = unstable_act;
var cloneElement$1 = cloneElement;
var createContext$1 = createContext;
var createElement$1 = createElement;
var createFactory$1 = createFactory;
var createRef = function () {
  var refObject = {
    current: null
  };
  return refObject;
};
var forwardRef$1 = forwardRef;
var isValidElement$1 = isValidElement;
var lazy$1 = lazy;
var memo$1 = memo;
var cache$1 = cache;
var startTransition$1 = startTransition;
var unstable_DebugTracingMode = REACT_DEBUG_TRACING_MODE_TYPE;
var unstable_LegacyHidden = REACT_LEGACY_HIDDEN_TYPE;
var unstable_Offscreen = REACT_OFFSCREEN_TYPE;
var unstable_Scope = REACT_SCOPE_TYPE;
var unstable_TracingMarker = REACT_TRACING_MARKER_TYPE;
var unstable_getCacheForType = function (resourceType) {
  var dispatcher = ReactCurrentDispatcher.current;
  if (dispatcher) {
    return dispatcher.getCacheForType(resourceType);
  } // Should only be called inside a render, so this is just a fallback
  return null;
};
var unstable_useCacheRefresh = function () {
  var dispatcher = ReactCurrentDispatcher.current;
  if (dispatcher) {
    return dispatcher.useCacheRefresh();
  } // Should only be called inside a render, so this is just a fallback
  return function () {
    return undefined;
  };
};
var useCallback$1 = useCallback;
var useContext$1 = useContext;
var useDebugValue$1 = useDebugValue;
var useDeferredValue$1 = useDeferredValue;
var useEffect$1 = useEffect;
var useId$1 = useId;
var useImperativeHandle$1 = useImperativeHandle;
var useInsertionEffect = useLayoutEffect;
var useLayoutEffect$1 = useLayoutEffect;
var useMemo$1 = useMemo;
var useReducer$1 = useReducer;
var useRef$1 = useRef;
var useState$1 = useState;
var useSyncExternalStore$2 = useSyncExternalStore$1;
var useTransition$1 = useTransition;
var use$1 = use;
var version = ReactVersion$2;
exports.Children = Children$1;
exports.Fragment = Fragment;
exports.Profiler = Profiler$1;
exports.PureComponent = PureComponent$1;
exports.StrictMode = StrictMode$1;
exports.Suspense = Suspense$1;
exports.SuspenseList = SuspenseList;
exports.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ReactSharedInternals$1;
exports.act = act;
exports.cache = cache$1;
exports.cloneElement = cloneElement$1;
exports.createContext = createContext$1;
exports.createElement = createElement$1;
exports.createFactory = createFactory$1;
exports.createRef = createRef;
exports.forwardRef = forwardRef$1;
exports.isValidElement = isValidElement$1;
exports.lazy = lazy$1;
exports.memo = memo$1;
exports.startTransition = startTransition$1;
exports.unstable_DebugTracingMode = unstable_DebugTracingMode;
exports.unstable_LegacyHidden = unstable_LegacyHidden;
exports.unstable_Offscreen = unstable_Offscreen;
exports.unstable_Scope = unstable_Scope;
exports.unstable_TracingMarker = unstable_TracingMarker;
exports.unstable_getCacheForType = unstable_getCacheForType;
exports.unstable_useCacheRefresh = unstable_useCacheRefresh;
exports.use = use$1;
exports.useCallback = useCallback$1;
exports.useContext = useContext$1;
exports.useDebugValue = useDebugValue$1;
exports.useDeferredValue = useDeferredValue$1;
exports.useEffect = useEffect$1;
exports.useId = useId$1;
exports.useImperativeHandle = useImperativeHandle$1;
exports.useInsertionEffect = useInsertionEffect;
exports.useLayoutEffect = useLayoutEffect$1;
exports.useMemo = useMemo$1;
exports.useReducer = useReducer$1;
exports.useRef = useRef$1;
exports.useState = useState$1;
exports.useSyncExternalStore = useSyncExternalStore$2;
exports.useTransition = useTransition$1;
exports.version = version;
  })();
}
