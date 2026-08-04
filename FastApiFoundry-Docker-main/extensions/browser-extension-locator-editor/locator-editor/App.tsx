import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Locator, LocatorsData } from './types';
import { DEFAULT_LOCATORS } from './constants';
import Header from './components/Header';
import LocatorList from './components/LocatorList';
import LocatorForm from './components/LocatorForm';
import { PlusCircleIcon, CodeBracketIcon, ArrowPathIcon } from './components/Icons';

const App: React.FC = () => {
    const [locatorsData, setLocatorsData] = useState<LocatorsData | null>(null);
    const [selectedLocatorKey, setSelectedLocatorKey] = useState<string | null>(null);
    const [isCreatingNew, setIsCreatingNew] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const isInitialMount = useRef(true);

    useEffect(() => {
        // FIX: Use (window as any).chrome to avoid TypeScript errors when @types/chrome is not available.
        (window as any).chrome.storage.local.get('locatorsData', (result: { locatorsData?: LocatorsData }) => {
            if (result.locatorsData) {
                setLocatorsData(result.locatorsData);
                 if (result.locatorsData.locators && Object.keys(result.locatorsData.locators).length > 0) {
                    setSelectedLocatorKey(Object.keys(result.locatorsData.locators)[0]);
                }
            } else {
                setLocatorsData(DEFAULT_LOCATORS);
                 if (DEFAULT_LOCATORS.locators && Object.keys(DEFAULT_LOCATORS.locators).length > 0) {
                    setSelectedLocatorKey(Object.keys(DEFAULT_LOCATORS.locators)[0]);
                }
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
            // FIX: Use (window as any).chrome to avoid TypeScript errors when @types/chrome is not available.
            (window as any).chrome.storage.local.set({ locatorsData });
        }
    }, [locatorsData]);

    const handleSelectLocator = useCallback((key: string) => {
        setSelectedLocatorKey(key);
        setIsCreatingNew(false);
    }, []);

    const handleCreateNew = () => {
        setSelectedLocatorKey(null);
        setIsCreatingNew(true);
    };

    const handleSaveLocator = (key: string, newLocator: Locator, originalKey?: string) => {
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
    
    const handleDeleteLocator = (key: string) => {
        if (!locatorsData) return;
        if (window.confirm(`Are you sure you want to delete the locator "${key}"?`)) {
            setLocatorsData(prevData => {
                if (!prevData) return null;
                const newLocators = { ...prevData.locators };
                delete newLocators[key];
                return { ...prevData, locators: newLocators };
            });

            if (selectedLocatorKey === key) {
                const remainingKeys = Object.keys(locatorsData.locators).filter(k => k !== key);
                setSelectedLocatorKey(remainingKeys.length > 0 ? remainingKeys[0] : null);
                setIsCreatingNew(false);
            }
        }
    };
    
    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
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
                    }
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                    alert("Invalid JSON file.");
                }
            };
            reader.readAsText(file);
        }
    };

    const getBackupFilename = () => {
        const now = new Date();
        const ts = now.toISOString().slice(2, 16).replace(/[-T:]/g, (c) => c === 'T' ? '_' : c === '-' ? '' : '');
        return `aiassist_config_backup_${ts}.json`;
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
        a.download = getBackupFilename();
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (isLoading || !locatorsData) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <ArrowPathIcon className="w-12 h-12 animate-spin text-teal-400" />
            </div>
        );
    }
    
    const selectedLocator = selectedLocatorKey ? locatorsData.locators[selectedLocatorKey] : null;

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
            <Header onFileUpload={handleFileUpload} onFileDownload={handleFileDownload} />
            <main className="flex flex-col md:flex-row" style={{ height: 'calc(100vh - 64px)' }}>
                <aside className="w-full md:w-1/3 lg:w-1/4 border-r border-gray-700 overflow-y-auto">
                     <div className="p-4">
                        <h2 className="text-lg font-semibold text-teal-400 mb-2">Supplier Prefix</h2>
                        <input
                            type="text"
                            value={locatorsData.supplier_prefix}
                            onChange={(e) => setLocatorsData(prev => prev ? ({...prev, supplier_prefix: e.target.value}) : null)}
                            className="w-full bg-gray-800 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                        />
                    </div>
                    <div className="p-4 border-t border-gray-700">
                         <button
                            onClick={handleCreateNew}
                            className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-4 rounded-md transition duration-200"
                        >
                            <PlusCircleIcon />
                            New Locator
                        </button>
                    </div>
                    <LocatorList 
                        locators={locatorsData.locators} 
                        selectedLocatorKey={selectedLocatorKey}
                        onSelect={handleSelectLocator}
                        onDelete={handleDeleteLocator}
                    />
                </aside>
                <section className="w-full md:w-2/3 lg:w-3/4 p-6 overflow-y-auto">
                    {isCreatingNew ? (
                         <LocatorForm 
                            onSave={handleSaveLocator}
                            isCreating={true}
                         />
                    ) : selectedLocator && selectedLocatorKey ? (
                        <LocatorForm 
                            key={selectedLocatorKey}
                            locator={selectedLocator} 
                            locatorKey={selectedLocatorKey}
                            onSave={handleSaveLocator}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <CodeBracketIcon className="w-24 h-24 mb-4" />
                            <h2 className="text-2xl font-bold">Select a locator to edit</h2>
                            <p>or create a new one to get started.</p>
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
};

export default App;