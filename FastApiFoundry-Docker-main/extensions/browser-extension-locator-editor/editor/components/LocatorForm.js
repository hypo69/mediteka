import { BY_STRATEGIES, IF_LIST_STRATEGIES, EMPTY_LOCATOR } from '../constants.js';
import { ClipboardIcon, CheckIcon } from './Icons.js';

const { useState, useEffect } = React;

const FormField = ({ label, children }) => React.createElement("div", { style: { marginBottom: '1rem' } },
    React.createElement("label", { style: { display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#9ca3af', marginBottom: '0.25rem' } }, label),
    children
);

const inputStyle = { width: '100%', backgroundColor: '#374151', border: '1px solid #4b5563', borderRadius: '0.375rem', padding: '8px 12px', color: '#f3f4f6' };
const formSectionStyle = { backgroundColor: '#1f2937', padding: '24px', borderRadius: '0.5rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)' };
const gridStyle = { ...formSectionStyle, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' };

const LocatorForm = ({ locator, locatorKey, onSave, isCreating = false }) => {
    const [formData, setFormData] = useState(locator || EMPTY_LOCATOR);
    const [currentKey, setCurrentKey] = useState(locatorKey || '');
    const [keyError, setKeyError] = useState('');
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        setFormData(locator || EMPTY_LOCATOR);
        setCurrentKey(locatorKey || '');
    }, [locator, locatorKey, isCreating]);

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        
        let processedValue = value;

        if (type === 'checkbox') {
            processedValue = e.target.checked;
        } else if (name === 'timeout') {
            processedValue = parseInt(value, 10) || 0;
        } else if (name === 'event' && value === "null") {
            processedValue = null;
        }

        setFormData(prev => ({ ...prev, [name]: processedValue }));
    };

    const handleKeyChange = (e) => {
        const newKey = e.target.value.replace(/\s/g, '_');
        setCurrentKey(newKey);
        if (!newKey) {
            setKeyError(chrome.i18n.getMessage("formErrorKeyEmpty"));
        } else {
            setKeyError('');
        }
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!currentKey) {
            setKeyError(chrome.i18n.getMessage("formErrorKeyEmpty"));
            return;
        }
        onSave(currentKey, formData, locatorKey);
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(formData.selector);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return React.createElement("form", { onSubmit: handleSubmit, style: { display: 'flex', flexDirection: 'column', gap: '24px' } },
        React.createElement("h2", { style: { fontSize: '1.5rem', fontWeight: 'bold', color: '#2dd4bf', borderBottom: '1px solid #374151', paddingBottom: '8px', marginBottom: '6px' } },
            isCreating ? chrome.i18n.getMessage("formCreateTitle") : chrome.i18n.getMessage("formEditTitle", [locatorKey])
        ),

        React.createElement("div", { style: formSectionStyle },
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelKey") },
                React.createElement("input", {
                    type: "text",
                    value: currentKey,
                    onChange: handleKeyChange,
                    placeholder: chrome.i18n.getMessage("formPlaceholderKey"),
                    style: { ...inputStyle, borderColor: keyError ? '#ef4444' : '#4b5563' },
                    required: true
                }),
                keyError && React.createElement("p", { style: { color: '#ef4444', fontSize: '0.75rem', marginTop: '4px' } }, keyError)
            ),

            React.createElement("div", { style: { position: 'relative' } },
                React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelSelector") },
                    React.createElement("textarea", {
                        name: "selector",
                        value: formData.selector,
                        onChange: handleChange,
                        rows: 4,
                        style: { ...inputStyle, fontFamily: 'monospace', fontSize: '0.875rem' },
                        placeholder: formData.by === 'XPATH' ? '//div[@id="example"]' : '#example'
                    })
                ),
                 React.createElement("button", {
                    type: "button",
                    onClick: copyToClipboard,
                    style: { position: 'absolute', top: '0', right: '0', marginTop: '30px', marginRight: '8px', padding: '8px', borderRadius: '0.375rem', backgroundColor: '#4b5563', border: 'none', cursor: 'pointer' },
                    title: chrome.i18n.getMessage("formCopyTooltip")
                },
                    copied ? React.createElement(CheckIcon, { style: { color: '#4ade80' } }) : React.createElement(ClipboardIcon, null)
                )
            ),

            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelDescription") },
                React.createElement("textarea", {
                    name: "locator_description",
                    value: formData.locator_description,
                    onChange: handleChange,
                    rows: 2,
                    style: inputStyle,
                    placeholder: chrome.i18n.getMessage("formPlaceholderDescription")
                })
            )
        ),
        
        React.createElement("div", { style: gridStyle },
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelFindBy") },
                React.createElement("select", { name: "by", value: formData.by, onChange: handleChange, style: inputStyle },
                    BY_STRATEGIES.map(s => React.createElement("option", { key: s, value: s }, s))
                )
            ),
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelAttribute") },
                React.createElement("input", { type: "text", name: "attribute", value: formData.attribute, onChange: handleChange, style: inputStyle })
            ),
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelIfList") },
                React.createElement("select", { name: "if_list", value: formData.if_list, onChange: handleChange, style: inputStyle },
                    IF_LIST_STRATEGIES.map(s => React.createElement("option", { key: s, value: s }, s))
                )
            ),
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelMultiSelectorStrategy") },
                React.createElement("input", { type: "text", name: "strategy_for_multiple_selectors", value: formData.strategy_for_multiple_selectors, onChange: handleChange, style: inputStyle })
            ),
            React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelTimeout") },
                React.createElement("input", { type: "number", name: "timeout", value: formData.timeout, onChange: handleChange, style: inputStyle })
            ),
             React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelTimeoutEvent") },
                React.createElement("input", { type: "text", name: "timeout_for_event", value: formData.timeout_for_event, onChange: handleChange, style: inputStyle })
            ),
            React.createElement("div", { style: { display: 'flex', alignItems: 'center', paddingTop: '20px', gap: '16px' } },
                React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelMandatory") },
                    React.createElement("input", { type: "checkbox", name: "mandatory", checked: formData.mandatory, onChange: handleChange, style: { height: '20px', width: '20px' } })
                ),
                React.createElement(FormField, { label: chrome.i18n.getMessage("formLabelIsEvent") },
                    React.createElement("input", { type: "checkbox", name: "event", checked: !!formData.event, onChange: handleChange, style: { height: '20px', width: '20px' } })
                )
            )
        ),

        React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', paddingTop: '16px' } },
            React.createElement("button", { type: "submit", style: { backgroundColor: '#0d9488', color: 'white', fontWeight: 'bold', padding: '8px 24px', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' } },
                chrome.i18n.getMessage("formSaveChangesBtn")
            )
        )
    );
};

export default LocatorForm;