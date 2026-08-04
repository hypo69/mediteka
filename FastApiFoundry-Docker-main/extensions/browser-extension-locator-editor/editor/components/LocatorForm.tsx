import React, { useState, useEffect } from 'react';
import { Locator, ByStrategy } from '../types';
import { BY_STRATEGIES, IF_LIST_STRATEGIES, EMPTY_LOCATOR } from '../constants';
import { ClipboardIcon, CheckIcon } from './Icons';

interface LocatorFormProps {
    locator?: Locator | null;
    locatorKey?: string;
    onSave: (key: string, newLocator: Locator, originalKey?: string) => void;
    isCreating?: boolean;
}

const FormField: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
    <div className="mb-4">
        <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
        {children}
    </div>
);

const LocatorForm: React.FC<LocatorFormProps> = ({ locator, locatorKey, onSave, isCreating = false }) => {
    const [formData, setFormData] = useState<Locator>(locator || EMPTY_LOCATOR);
    const [currentKey, setCurrentKey] = useState(locatorKey || '');
    const [keyError, setKeyError] = useState('');
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        setFormData(locator || EMPTY_LOCATOR);
        setCurrentKey(locatorKey || '');
    }, [locator, locatorKey, isCreating]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target;
        
        let processedValue: string | number | boolean | null = value;

        if (type === 'checkbox') {
            processedValue = (e.target as HTMLInputElement).checked;
        } else if (name === 'timeout') {
            processedValue = parseInt(value, 10) || 0;
        } else if (name === 'event' && value === "null") {
            processedValue = null;
        }

        setFormData(prev => ({ ...prev, [name]: processedValue }));
    };

    const handleKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newKey = e.target.value.replace(/\s/g, '_');
        setCurrentKey(newKey);
        if (!newKey) {
            setKeyError('Locator key cannot be empty.');
        } else {
            setKeyError('');
        }
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentKey) {
            setKeyError('Locator key cannot be empty.');
            return;
        }
        onSave(currentKey, formData, locatorKey);
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(formData.selector);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <h2 className="text-2xl font-bold text-teal-400 border-b border-gray-700 pb-2 mb-6">
                {isCreating ? 'Create New Locator' : `Editing: ${locatorKey}`}
            </h2>

            <div className="bg-gray-800 p-6 rounded-lg shadow-md">
                <FormField label="Locator Key">
                    <input
                        type="text"
                        value={currentKey}
                        onChange={handleKeyChange}
                        placeholder="e.g., product_name"
                        className={`w-full bg-gray-700 border ${keyError ? 'border-red-500' : 'border-gray-600'} rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none`}
                        required
                    />
                    {keyError && <p className="text-red-500 text-xs mt-1">{keyError}</p>}
                </FormField>

                <div className="relative">
                    <FormField label="Selector">
                        <textarea
                            name="selector"
                            value={formData.selector}
                            onChange={handleChange}
                            rows={4}
                            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 font-mono text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                            placeholder={formData.by === 'XPATH' ? '//div[@id="example"]' : '#example'}
                        />
                    </FormField>
                     <button
                        type="button"
                        onClick={copyToClipboard}
                        className="absolute top-0 right-0 mt-8 mr-2 p-2 rounded-md bg-gray-600 hover:bg-gray-500 transition-colors"
                        title="Copy selector to clipboard"
                    >
                        {copied ? <CheckIcon className="text-green-400" /> : <ClipboardIcon />}
                    </button>
                </div>


                <FormField label="Description">
                    <textarea
                        name="locator_description"
                        value={formData.locator_description}
                        onChange={handleChange}
                        rows={2}
                        className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                        placeholder="A brief description of this locator"
                    />
                </FormField>
            </div>
            
             <div className="bg-gray-800 p-6 rounded-lg shadow-md grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                 <FormField label="Find By">
                    <select name="by" value={formData.by} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none">
                        {BY_STRATEGIES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </FormField>
                <FormField label="Attribute to Get">
                    <input type="text" name="attribute" value={formData.attribute} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
                </FormField>
                <FormField label="If List Found">
                    <select name="if_list" value={formData.if_list} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none">
                        {IF_LIST_STRATEGIES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </FormField>
                <FormField label="Strategy for Multiple Selectors">
                    <input type="text" name="strategy_for_multiple_selectors" value={formData.strategy_for_multiple_selectors} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
                </FormField>
                <FormField label="Timeout (ms)">
                    <input type="number" name="timeout" value={formData.timeout} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
                </FormField>
                 <FormField label="Timeout Event Type">
                    <input type="text" name="timeout_for_event" value={formData.timeout_for_event} onChange={handleChange} className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
                </FormField>
                 <div className="flex items-center pt-5 gap-4">
                    <FormField label="Mandatory">
                        <label className="flex items-center cursor-pointer">
                            <input type="checkbox" name="mandatory" checked={formData.mandatory} onChange={handleChange} className="form-checkbox h-5 w-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500" />
                        </label>
                    </FormField>
                    <FormField label="Is Event?">
                        <label className="flex items-center cursor-pointer">
                            <input type="checkbox" name="event" checked={!!formData.event} onChange={handleChange} className="form-checkbox h-5 w-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500" />
                         </label>
                    </FormField>
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <button type="submit" className="bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-6 rounded-md transition duration-200">
                    Save Changes
                </button>
            </div>
        </form>
    );
};

export default LocatorForm;