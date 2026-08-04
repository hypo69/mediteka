
import React, { useState, useCallback, useEffect } from 'react';
import { Locator, LocatorsData } from './types';
import { DEFAULT_LOCATORS } from './constants';
import Header from './components/Header';
import LocatorList from './components/LocatorList';
import LocatorForm from './components/LocatorForm';
import { PlusCircleIcon, CodeBracketIcon } from './components/Icons';

const App: React.FC = () => {
    const [locatorsData, setLocatorsData] = useState<LocatorsData>(DEFAULT_LOCATORS);
    const [selectedLocatorKey, setSelectedLocatorKey] = useState<string | null>(null);
    const [isCreatingNew, setIsCreatingNew] = useState(false);

    useEffect(() => {
        if (locatorsData.locators && Object.keys(locatorsData.locators).length > 0) {
            setSelectedLocatorKey(Object.keys(locatorsData.locators)[0]);
        }
    }, []);

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
        if (window.confirm(`Are you sure you want to delete the locator "${key}"?`)) {
            setLocatorsData(prevData => {
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
                        setLocatorsData({ supplier_prefix, locators });
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

    const handleFileDownload = () => {
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
                            onChange={(e) => setLocatorsData(prev => ({...prev, supplier_prefix: e.target.value}))}
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
