/**
 * @license React
 * react-dom.development.js
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

var React = require('react');
var Scheduler = require('scheduler');

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

var ReactDOMSharedInternals = {
  Dispatcher: {
    current: null
  }
};

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
var previousWasCompleted = false;
var isSchedulerPaused = false;
var isLoopRunning = false;
var ShouldYield = Scheduler.unstable_shouldYield;
var ImmediatePriority = 99;
var UserBlockingPriority = 98;
var NormalPriority = 97;
var LowPriority = 96;
var IdlePriority = 95; // NoPriority is the absence of priority. Also React-only.
var NoPriority = 90;
var initialTimeMs = Scheduler.unstable_now(); // If the scheduler yields or throws, exit the current work loop.
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
var scheduleTimeout = typeof setTimeout === 'function' ? setTimeout : undefined;
var cancelTimeout = typeof clearTimeout === 'function' ? clearTimeout : undefined;
var noTimeout = -1; // -------------------
var supportsMutation = true;
function getPublicInstance(instance) {
  return instance;
}
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
function get(key) {
  return key._reactInternals;
}
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
var getComponentNameFromType = getComponentNameFromType;
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
var didWarnAboutStringRefs;
var ownerHasKeyUseWarning;
var ownerHasFunctionUseWarning;
var warnForMissingKey = function (child, returnFiber) {};
didWarnAboutMaps = false;
didWarnAboutGenerators = false;
didWarnAboutStringRefs = {};
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
var NoLane = /*                          */0;
var SyncLane = /*                        */1;
function requestCurrentTransition() {
  return ReactCurrentBatchConfig.transition;
}
var ReactCurrentActQueue$1 = ReactSharedInternals.ReactCurrentActQueue;
var DefaultSuspenseCallback$1 = function (res) {
  // To be implemented.
};

// TODO: Finish this WIP.
var valueStack = [];
var fiberStack = [];
function getFiberCurrentPropsFromNode(node) {
  return node[internalPropsKey] || null;
}
function updateFiberProps(node, props) {
  node[internalPropsKey] = props;
}
var ReactDOM$2 = {
  createRoot: createRoot,
  hydrateRoot: hydrateRoot,
  // TODO: The new createRoot API is framework-specific. We should probably
  // remove this from the renderer level.
  unstable_batchedUpdates: batchedUpdates,
  unstable_createEventHandle: createEventHandle,
  unstable_flushSync: flushSync,
  unstable_isNewReconciler: true,
  version: ReactVersion
};
var foundDevTools = 0;
var testAndNorms = {};
var topLevelUpdateWarnings;
var warnedAboutHydrateAPI = false;
topLevelUpdateWarnings = new Set();
function getContextForSubtree(parentComponent) {
  if (!parentComponent) {
    return emptyObject;
  }
  var fiber = get(parentComponent);
  var parentContext = findCurrentUnmaskedContext(fiber);
  return parentContext;
}
function createRoot(container, options) {
  if (!isValidContainer(container)) {
    throw new Error('createRoot(...): Target container is not a DOM element.');
  }
  warnIfReactDOMContainerInDEV(container);
  var isStrictMode = false;
  var concurrentUpdatesByDefault = false;
  var identifierPrefix = '';
  var onRecoverableError = defaultOnRecoverableError;
  var transitionCallbacks = null;
  if (options !== null && options !== undefined) {
    if (options.unstable_strictMode === true) {
      isStrictMode = true;
    }
    if (options.unstable_concurrentUpdatesByDefault === true) {
      concurrentUpdatesByDefault = true;
    }
    if (options.identifierPrefix !== undefined) {
      identifierPrefix = options.identifierPrefix;
    }
    if (options.onRecoverableError !== undefined) {
      onRecoverableError = options.onRecoverableError;
    }
    if (options.unstable_transitionCallbacks !== undefined) {
      transitionCallbacks = options.unstable_transitionCallbacks;
    }
  }
  var root = createContainer(container, ConcurrentRoot, null, isStrictMode, concurrentUpdatesByDefault, identifierPrefix, onRecoverableError, transitionCallbacks);
  markContainerAsRoot(root.current, container);
  var rootContainerElement = container.nodeType === COMMENT_NODE ? container.parentNode : container;
  listenToAllSupportedEvents(rootContainerElement);
  return new ReactDOMRoot(root);
}
function hydrateRoot(container, initialChildren, options) {
  if (!isValidContainer(container)) {
    throw new Error('hydrateRoot(...): Target container is not a DOM element.');
  }
  warnIfReactDOMContainerInDEV(container);
  if (warnedAboutHydrateAPI === false) {
    warnedAboutHydrateAPI = true;
    warn('The hydrateRoot API is still experimental and may change. It is only intended for experimental use in frameworks like Next.js');
  } // For now, hydrateRoot is always strict mode.
  var isStrictMode = true;
  var concurrentUpdatesByDefault = false;
  var identifierPrefix = '';
  var onRecoverableError = defaultOnRecoverableError;
  var transitionCallbacks = null;
  if (options !== null && options !== undefined) {
    if (options.unstable_concurrentUpdatesByDefault === true) {
      concurrentUpdatesByDefault = true;
    }
    if (options.identifierPrefix !== undefined) {
      identifierPrefix = options.identifierPrefix;
    }
    if (options.onRecoverableError !== undefined) {
      onRecoverableError = options.onRecoverableError;
    }
    if (options.unstable_transitionCallbacks !== undefined) {
      transitionCallbacks = options.unstable_transitionCallbacks;
    }
  }
  var hydrationCallbacks = null;
  var root = createHydrationContainer(initialChildren, null, container, ConcurrentRoot, hydrationCallbacks, isStrictMode, concurrentUpdatesByDefault, identifierPrefix, onRecoverableError, transitionCallbacks);
  markContainerAsRoot(root.current, container); // This can't be a comment node since hydration doesn't work on comment nodes anyway.
  listenToAllSupportedEvents(container);
  return new ReactDOMHydrationRoot(root);
}
function render(element, container, callback) {
  return legacyRenderSubtreeIntoContainer(null, element, container, false, callback);
}
function unstable_renderSubtreeIntoContainer(parentComponent, element, containerNode, callback) {
  return legacyRenderSubtreeIntoContainer(parentComponent, element, containerNode, false, callback);
}
function unmountComponentAtNode(container) {
  var root = getClosestInstanceFromNode(container);
  if (root != null) {
    var containerFiber = root.child;
    if (containerFiber != null) {
      var Grandparent = containerFiber.return.return;
      if (Grandparent != null) {
        var containerParent = Grandparent.stateNode;
        if (containerParent != null && containerParent.containerInfo === container) {
          unbatchedUpdates(function () {
            updateContainer(null, containerFiber.return, null, null);
          });
          return true;
        }
      }
    }
  }
  return false;
}
var Internals = {
  // Keep in sync with ReactTestUtils.js.
  // Used by ReactTestUtils. It will be deleted in a future release.
  Events: [getInstanceFromNode$1, getNodeFromInstance$1, getFiberCurrentPropsFromNode, enqueueStateRestore, restoreStateIfNeeded, batchedUpdates]
};
var foundDevTools$1 = 0;
var testAndNorms$1 = {};
var topLevelUpdateWarnings$1;
var warnedAboutHydrateAPI$1 = false;
topLevelUpdateWarnings$1 = new Set();
var findDOMNode = function (componentOrElement) {
  if (componentOrElement == null) {
    return null;
  }
  if (componentOrElement.nodeType === 1) {
    return componentOrElement;
  }
  var fiber = get(componentOrElement);
  if (fiber !== undefined) {
    return findHostInstanceByFiber(fiber);
  }
  if (typeof componentOrElement.render === 'function') {
    throw new Error('Unable to find node on an unmounted component.');
  } else {
    throw new Error("Element appears to be neither ReactComponent nor DOMNode. Keys: " + Object.keys(componentOrElement));
  }
};
var flushSync$1 = flushSync;
var hydrate = function (element, container, callback) {
  if (!isValidContainer(container)) {
    throw new Error('Target container is not a DOM element.');
  }
  warnIfReactDOMContainerInDEV(container); // TODO: Your existing integration logic should go here!
  var root = legacyCreateRootFromDOMContainer(container, false, shouldHydrateDueToLegacyHeuristic(container));
  legacyRenderSubtreeIntoContainer(null, element, root, true, callback);
  return getPublicRootInstance(root);
};
var render$1 = render;
var unmountComponentAtNode$1 = unmountComponentAtNode;
var unstable_batchedUpdates$1 = batchedUpdates;
var unstable_createPortal = function (children, container) {
  var key = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : null;
  if (!isValidContainer(container)) {
    throw new Error('Target container is not a DOM element.');
  } // TODO: pass ReactDOM portal implementation as third argument
  return createPortal(children, container, null, key);
};
var unstable_renderSubtreeIntoContainer$1 = unstable_renderSubtreeIntoContainer;
var version = ReactVersion;
exports.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Internals;
exports.createPortal = unstable_createPortal;
exports.createRoot = createRoot;
exports.findDOMNode = findDOMNode;
exports.flushSync = flushSync$1;
exports.hydrate = hydrate;
exports.hydrateRoot = hydrateRoot;
exports.render = render$1;
exports.unmountComponentAtNode = unmountComponentAtNode$1;
exports.unstable_batchedUpdates = unstable_batchedUpdates$1;
exports.unstable_renderSubtreeIntoContainer = unstable_renderSubtreeIntoContainer$1;
exports.version = version;
  })();
}
