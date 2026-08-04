import React from 'react';
import ReactDOM from 'react-dom/client';

const Popup = () => {
    const openEditor = () => {
        // Use (window as any).chrome to avoid TypeScript errors when @types/chrome is not available.
        (window as any).chrome.tabs.create({
            url: (window as any).chrome.runtime.getURL('editor/editor.html')
        });
        window.close(); // Close the popup after opening the tab
    };

    const buttonStyle: React.CSSProperties = {
        backgroundColor: '#20c997', // teal
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '16px',
        fontWeight: 'bold',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
    };
    
    const h1Style: React.CSSProperties = {
        fontSize: '18px',
        marginBottom: '16px',
        textAlign: 'center'
    };

    const svgIcon = (
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: '24px', height: '24px' }}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
        </svg>
    );

    return (
        <>
            <h1 style={h1Style}>Locator Editor</h1>
            <button onClick={openEditor} style={buttonStyle}>
                {svgIcon}
                Open Editor
            </button>
        </>
    );
};

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}
const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <Popup />
  </React.StrictMode>
);