# -*- coding: utf-8 -*-
# =============================================================================
# File: extensions/browser-extension-locator-editor/editor/App.js
# Version: 0.6.0
# Changes in 0.6.0:
#   - Added fetchApi helper for standardized response handling
# =============================================================================

import { DEFAULT_LOCATORS } from './constants.js';
import Header from './components/Header.js';
import LocatorList from './components/LocatorList.js';
import LocatorForm from './components/LocatorForm.js';
import { PlusCircleIcon, CodeBracketIcon, ArrowPathIcon } from './components/Icons.js';

const { useState, useCallback, useEffect, useRef } = React;

const App = () => {
    // Helper to handle the new backend response format consistently
    const fetchApi = async (endpoint, options = {}) => {
        try {
            const response = await fetch(`http://localhost:9696/api/v1${endpoint}`, {
                ...options,
                headers: { 'Content-Type': 'application/json', ...options.headers },
            });
            const data = await response.json();
            if (!data.success) {
                alert(chrome.i18n.getMessage("apiError", [data.error]) || data.error);
                return null;
            }
            return data;
        } catch (err) {
            console.error("API Call failed:", err);
            return null;
        }
    };

    const [locatorsData, setLocatorsData] = useState(null);
    const [selectedLocatorKey, setSelectedLocatorKey] = useState(null);
    const [isCreatingNew, setIsCreatingNew] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const isInitialMount = useRef(true);

    useEffect(() => {
        chrome.storage.local.get('locatorsData', (result) => {
            if (result.locatorsData && Object.keys(result.locatorsData.locators).length > 0) {
                setLocatorsData(result.locatorsData);
                setSelectedLocatorKey(Object.keys(result.locatorsData.locators)[0]);
            } else {
                setLocatorsData(DEFAULT_LOCATORS);
                setSelectedLocatorKey(Object.keys(DEFAULT_LOCATORS.locators)[0]);
            }
            setIsLoading(false);
        });
    }, []);

    useEffect(() => {
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }
        if (locatorsData) {
            chrome.storage.local.set({ locatorsData });
        }
    }, [locatorsData]);

    const handleSelectLocator = useCallback((key) => {
        setSelectedLocatorKey(key);
        setIsCreatingNew(false);
    }, []);

    const handleCreateNew = () => {
        setSelectedLocatorKey(null);
        setIsCreatingNew(true);
    };

    const handleSaveLocator = (key, newLocator, originalKey) => {
        const isNew = !originalKey;
        setLocatorsData(prevData => {
            if (!prevData) return null;
            const newLocators = { ...prevData.locators };

            if (originalKey && originalKey !== key) {
                delete newLocators[originalKey];
            }
            
            newLocators[key] = newLocator;

            return { ...prevData, locators: newLocators };
        });
        setSelectedLocatorKey(key);
        setIsCreatingNew(false);
    };
    
    const handleDeleteLocator = (key) => {
        if (!locatorsData) return;
        if (window.confirm(chrome.i18n.getMessage("confirmDeleteLocator", [key]))) {
            const newLocators = { ...locatorsData.locators };
            delete newLocators[key];
            
            setLocatorsData(prevData => {
                if (!prevData) return null;
                return { ...prevData, locators: newLocators };
            });

            if (selectedLocatorKey === key) {
                const remainingKeys = Object.keys(newLocators);
                setSelectedLocatorKey(remainingKeys.length > 0 ? remainingKeys[0] : null);
                setIsCreatingNew(false);
            }
        }
    };
    
    const handleFileUpload = (event) => {
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const content = e.target?.result;
                    if (typeof content === 'string') {
                        const parsedJson = JSON.parse(content);
                        const { supplier_prefix, ...locators } = parsedJson;
                        const newLocatorsData = { supplier_prefix: supplier_prefix || "", locators: locators || {} };
                        setLocatorsData(newLocatorsData);

                        const firstKey = Object.keys(locators)[0];
                        if (firstKey) {
                            handleSelectLocator(firstKey);
                        } else {
                            setSelectedLocatorKey(null);
                        }
                        alert(chrome.i18n.getMessage("alertImportSuccess"));
                    }
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                    alert(chrome.i18n.getMessage("alertInvalidJson"));
                }
            };
            reader.readAsText(file);
        }
    };

    const handleFileDownload = () => {
        if (!locatorsData) return;
        const {locators, ...rest} = locatorsData;
        const dataToDownload = {...rest, ...locators};
        const jsonString = JSON.stringify(dataToDownload, null, 2);
        const blob = new Blob([jsonString], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${locatorsData.supplier_prefix || 'locators'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (isLoading || !locatorsData) {
        return React.createElement("div", {
          style: { display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: '#111827' }
        }, React.createElement(ArrowPathIcon, { style: { width: '48px', height: '48px', color: '#2dd4bf' /* teal-400 */ } }));
    }
    
    const selectedLocator = selectedLocatorKey ? locatorsData.locators[selectedLocatorKey] : null;

    // Basic styling to mimic the original layout
    const mainStyles = { display: 'flex', height: 'calc(100vh - 64px)', flexDirection: 'row' };
    const asideStyles = { width: '300px', borderRight: '1px solid #374151', overflowY: 'auto', display: 'flex', flexDirection: 'column', flexShrink: 0 };
    const sectionStyles = { flexGrow: 1, padding: '24px', overflowY: 'auto' };
    const emptyStateStyles = { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' };
    const inputStyle = { width: '100%', backgroundColor: '#1f2937', border: '1px solid #4b5563', borderRadius: '0.375rem', padding: '8px 12px', color: '#f3f4f6', outline: 'none' };
    const buttonStyle = { width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', backgroundColor: '#0d9488', color: 'white', fontWeight: 'bold', padding: '8px 16px', borderRadius: '0.375rem', border: 'none', cursor: 'pointer', transition: 'background-color 0.2s' };


    return React.createElement("div", {
        style: { minHeight: '100vh', backgroundColor: '#111827', color: '#f3f4f6', fontFamily: 'sans-serif' }
    }, 
        React.createElement(Header, { onFileUpload: handleFileUpload, onFileDownload: handleFileDownload }),
        React.createElement("main", { style: mainStyles },
            React.createElement("aside", { style: asideStyles },
                 React.createElement("div", { style: { padding: '16px' } },
                    React.createElement("h2", { style: { fontSize: '1.125rem', fontWeight: '600', color: '#2dd4bf', marginBottom: '8px' } }, chrome.i18n.getMessage("sidebarSupplierPrefix")),
                    React.createElement("input", {
                        type: "text",
                        value: locatorsData.supplier_prefix,
                        onChange: (e) => setLocatorsData(prev => prev ? ({...prev, supplier_prefix: e.target.value}) : null),
                        style: inputStyle
                    })
                ),
                React.createElement("div", { style: { padding: '16px', borderTop: '1px solid #374151' } },
                     React.createElement("button", {
                        onClick: handleCreateNew,
                        style: buttonStyle,
                        onMouseEnter: e => e.currentTarget.style.backgroundColor = '#0f766e',
                        onMouseLeave: e => e.currentTarget.style.backgroundColor = '#0d9488'
                    },
                        React.createElement(PlusCircleIcon, null),
                        chrome.i18n.getMessage("sidebarNewLocatorBtn")
                    )
                ),
                React.createElement(LocatorList, { 
                    locators: locatorsData.locators, 
                    selectedLocatorKey: selectedLocatorKey,
                    onSelect: handleSelectLocator,
                    onDelete: handleDeleteLocator
                })
            ),
            React.createElement("section", { style: sectionStyles },
                isCreatingNew ? 
                     React.createElement(LocatorForm, { 
                        onSave: handleSaveLocator,
                        isCreating: true
                     })
                 : selectedLocator && selectedLocatorKey ? 
                    React.createElement(LocatorForm, { 
                        key: selectedLocatorKey,
                        locator: selectedLocator, 
                        locatorKey: selectedLocatorKey,
                        onSave: handleSaveLocator
                    })
                 : 
                    React.createElement("div", { style: emptyStateStyles },
                         Object.keys(locatorsData.locators).length === 0 ? 
                            React.createElement(React.Fragment, null,
                                React.createElement("h2", { style: { fontSize: '1.5rem', fontWeight: 'bold' } }, chrome.i18n.getMessage("emptyStateNoLocatorsTitle")),
                                React.createElement("p", { style: { marginTop: '8px' } }, chrome.i18n.getMessage("emptyStateNoLocatorsSubtitle"))
                            )
                         : 
                            React.createElement(React.Fragment, null,
                                React.createElement(CodeBracketIcon, { style: { width: '96px', height: '96px', marginBottom: '16px' } }),
                                React.createElement("h2", { style: { fontSize: '1.5rem', fontWeight: 'bold' } }, chrome.i18n.getMessage("emptyStateSelectLocatorTitle")),
                                React.createElement("p", null, chrome.i18n.getMessage("emptyStateSelectLocatorSubtitle"))
                            )
                        
                    )
                
            )
        )
    );
};

export default App;