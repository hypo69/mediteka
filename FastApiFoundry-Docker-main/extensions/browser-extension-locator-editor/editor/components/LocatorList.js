import { TrashIcon, ChevronRightIcon } from './Icons.js';

const LocatorList = ({ locators, selectedLocatorKey, onSelect, onDelete }) => {
    
    const navStyle = { flex: 1, overflowY: 'auto' };
    const h2Style = { padding: '8px 16px', fontSize: '1.125rem', fontWeight: '600', color: '#2dd4bf', position: 'sticky', top: 0, backgroundColor: '#111827' };
    
    return React.createElement("nav", { style: navStyle },
        React.createElement("h2", { style: h2Style }, chrome.i18n.getMessage("sidebarLocatorsHeading")),
        React.createElement("ul", null,
            Object.keys(locators).sort().map(key => {
                const isSelected = selectedLocatorKey === key;
                const itemStyle = {
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    backgroundColor: isSelected ? 'rgba(13, 148, 136, 0.5)' : 'transparent',
                    color: isSelected ? 'white' : '#d1d5db',
                };
                
                return React.createElement("li", { key: key, style: { padding: '4px 8px' } },
                    React.createElement("div", {
                        onClick: () => onSelect(key),
                        style: itemStyle,
                        onMouseEnter: e => { if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(55, 65, 81, 0.5)'; },
                        onMouseLeave: e => { if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent'; }
                    },
                        React.createElement("div", { style: { display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' } },
                           isSelected && React.createElement(ChevronRightIcon, { style: { width: '20px', height: '20px', color: '#2dd4bf', flexShrink: 0 } }),
                           React.createElement("span", { style: { fontWeight: '500', marginLeft: isSelected ? '0' : '28px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' } }, key)
                        ),
                        React.createElement("button", {
                            onClick: (e) => {
                                e.stopPropagation();
                                onDelete(key);
                            },
                            style: { padding: '4px', borderRadius: '9999px', color: '#9ca3af', flexShrink: 0, border: 'none', background: 'transparent', cursor: 'pointer' },
                            title: chrome.i18n.getMessage("sidebarDeleteLocatorTitle", [key])
                        },
                            React.createElement(TrashIcon, null)
                        )
                    )
                )
            })
        )
    );
};

export default LocatorList;