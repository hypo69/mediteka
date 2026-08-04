import { CodeBracketSquareIcon, DocumentArrowUpIcon, DocumentArrowDownIcon } from './Icons.js';

const { useRef } = React;

const Header = ({ onFileUpload, onFileDownload }) => {
    const fileInputRef = useRef(null);

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };
    
    const styles = {
        header: {
            backgroundColor: '#1f2937', // gray-800
            borderBottom: '1px solid #374151', // gray-700
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            height: '64px',
            flexShrink: 0
        },
        logoContainer: { display: 'flex', alignItems: 'center', gap: '12px' },
        title: { fontSize: '1.25rem', fontWeight: 'bold', color: 'white' },
        buttonContainer: { display: 'flex', alignItems: 'center', gap: '16px' },
        baseButton: { 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            color: 'white', 
            fontWeight: '600', 
            padding: '8px 16px', 
            borderRadius: '6px', 
            border: 'none', 
            cursor: 'pointer',
            transition: 'background-color 0.2s'
        },
        importButton: {
            backgroundColor: '#374151' /* gray-700 */ 
        },
        exportButton: {
            backgroundColor: '#0d9488' /* teal-600 */ 
        }
    };

    return React.createElement("header", { style: styles.header },
        React.createElement("div", { style: styles.logoContainer },
            React.createElement(CodeBracketSquareIcon, { style: { width: '32px', height: '32px', color: '#2dd4bf' } }),
            React.createElement("h1", { style: styles.title }, chrome.i18n.getMessage("appName"))
        ),
        React.createElement("div", { style: styles.buttonContainer },
            React.createElement("input", {
                type: "file",
                ref: fileInputRef,
                onChange: onFileUpload,
                style: { display: 'none' },
                accept: ".json"
            }),
            React.createElement("button", {
                onClick: handleUploadClick,
                style: {...styles.baseButton, ...styles.importButton },
                onMouseEnter: e => e.currentTarget.style.backgroundColor = '#4b5563', // gray-600
                onMouseLeave: e => e.currentTarget.style.backgroundColor = '#374151', // gray-700
                title: chrome.i18n.getMessage("headerImportTitle")
            },
                React.createElement(DocumentArrowUpIcon, null),
                chrome.i18n.getMessage("headerImportBtn")
            ),
            React.createElement("button", {
                onClick: onFileDownload,
                style: {...styles.baseButton, ...styles.exportButton },
                onMouseEnter: e => e.currentTarget.style.backgroundColor = '#0f766e', // teal-700
                onMouseLeave: e => e.currentTarget.style.backgroundColor = '#0d9488', // teal-600
                title: chrome.i18n.getMessage("headerExportTitle")
            },
                React.createElement(DocumentArrowDownIcon, null),
                chrome.i18n.getMessage("headerExportBtn")
            )
        )
    );
};

export default Header;