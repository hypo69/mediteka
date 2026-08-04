
import React from 'react';
import { Locator } from '../types';
import { TrashIcon, ChevronRightIcon } from './Icons';

interface LocatorListProps {
    locators: Record<string, Locator>;
    selectedLocatorKey: string | null;
    onSelect: (key: string) => void;
    onDelete: (key: string) => void;
}

const LocatorList: React.FC<LocatorListProps> = ({ locators, selectedLocatorKey, onSelect, onDelete }) => {
    return (
        <nav className="flex-1">
            <h2 className="px-4 pt-2 text-lg font-semibold text-teal-400">Locators</h2>
            <ul>
                {Object.keys(locators).sort().map(key => (
                    <li key={key} className="px-2 py-1">
                        <div
                            onClick={() => onSelect(key)}
                            className={`flex items-center justify-between p-2 rounded-md cursor-pointer transition-colors duration-150 ${
                                selectedLocatorKey === key ? 'bg-teal-800/50 text-white' : 'hover:bg-gray-700/50 text-gray-300'
                            }`}
                        >
                            <div className="flex items-center gap-2">
                               {selectedLocatorKey === key && <ChevronRightIcon className="w-5 h-5 text-teal-400"/>}
                                <span className={`font-medium ${selectedLocatorKey !== key ? 'ml-7' : ''}`}>{key}</span>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDelete(key);
                                }}
                                className="p-1 rounded-full hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors"
                                title={`Delete ${key}`}
                            >
                                <TrashIcon />
                            </button>
                        </div>
                    </li>
                ))}
            </ul>
        </nav>
    );
};

export default LocatorList;
