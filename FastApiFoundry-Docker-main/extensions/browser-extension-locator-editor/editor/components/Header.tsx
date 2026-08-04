import React, { useRef } from 'react';
import { CodeBracketSquareIcon, DocumentArrowUpIcon, DocumentArrowDownIcon } from './Icons';

interface HeaderProps {
    onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
    onFileDownload: () => void;
}

const Header: React.FC<HeaderProps> = ({ onFileUpload, onFileDownload }) => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <header className="bg-gray-800 border-b border-gray-700 shadow-lg p-4 flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
                <CodeBracketSquareIcon className="w-8 h-8 text-teal-400" />
                <h1 className="text-xl font-bold text-white">Locator Editor</h1>
            </div>
            <div className="flex items-center gap-4">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={onFileUpload}
                    className="hidden"
                    accept=".json"
                />
                <button
                    onClick={handleUploadClick}
                    className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
                    title="Import JSON"
                >
                    <DocumentArrowUpIcon />
                    Import
                </button>
                <button
                    onClick={onFileDownload}
                    className="flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
                    title="Export JSON"
                >
                    <DocumentArrowDownIcon />
                    Export
                </button>
            </div>
        </header>
    );
};

export default Header;