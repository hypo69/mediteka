const Popup = () => {
    const openEditor = () => {
        chrome.tabs.create({
            url: chrome.runtime.getURL('editor/editor.html')
        });
        window.close();
    };

    const styles = {
        container: {
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
        },
        title: {
            fontSize: '18px',
            marginBottom: '16px',
            textAlign: 'center',
            color: '#f3f4f6'
        },
        button: {
            backgroundColor: '#0d9488', // teal-600
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'background-color 0.2s'
        },
        icon: {
            width: '24px',
            height: '24px'
        }
    };

    const svgIcon = React.createElement("svg", {
      xmlns: "http://www.w3.org/2000/svg",
      fill: "none",
      viewBox: "0 0 24 24",
      strokeWidth: 1.5,
      stroke: "currentColor",
      style: styles.icon
    }, React.createElement("path", {
      strokeLinecap: "round",
      strokeLinejoin: "round",
      d: "M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z"
    }));

    return React.createElement("div", { style: styles.container },
        React.createElement("h1", { style: styles.title }, chrome.i18n.getMessage("popupTitle")),
        React.createElement("button", {
            onClick: openEditor,
            style: styles.button,
            onMouseEnter: e => e.currentTarget.style.backgroundColor = '#0f766e', // teal-700
            onMouseLeave: e => e.currentTarget.style.backgroundColor = '#0d9488'  // teal-600
        },
            svgIcon,
            chrome.i18n.getMessage("openEditorBtn")
        )
    );
};

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}
const root = ReactDOM.createRoot(rootElement);
root.render(
  React.createElement(React.StrictMode, null, React.createElement(Popup, null))
);