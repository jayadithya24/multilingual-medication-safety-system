import { useState, useEffect, useRef } from "react";

/**
 * Language Selector Component
 * Allows user to select language for OCR and drug information display
 */
function LanguageSelector({ selectedLanguage, onLanguageChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: "en", name: "English", nativeName: "English" },
    { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ" },
    { code: "te", name: "Tulu", nativeName: "ತುಳು" }
  ];

  const handleSelect = (langCode) => {
    onLanguageChange(langCode);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const dropdownRef = useRef(null);

  const currentLang = languages.find(l => l.code === selectedLanguage) || languages[0];

  return (
    <div className="language-selector" ref={dropdownRef}>
      <button
        className="language-selector__button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Current language: ${currentLang.name}`}
      >
        <span className="language-selector__flag">{currentLang.nativeName}</span>
        <span className="language-selector__arrow">▼</span>
      </button>

      {isOpen && (
        <ul className="language-selector__dropdown" role="listbox">
          {languages.map(lang => (
            <li
              key={lang.code}
              className={`language-selector__option ${lang.code === selectedLanguage ? "selected" : ""}`}
              role="option"
              aria-selected={lang.code === selectedLanguage}
              onClick={() => handleSelect(lang.code)}
            >
              <span className="language-selector__option-native">{lang.nativeName}</span>
              <span className="language-selector__option-english">({lang.name})</span>
            </li>
          ))}
        </ul>
      )}

      <style>{`
        .language-selector {
          position: relative;
          display: inline-block;
        }
        .language-selector__button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: #f5f5f5;
          border: 1px solid #ddd;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          color: #333;
          transition: all 0.2s ease;
        }
        .language-selector__button:hover {
          background: #eee;
          border-color: #ccc;
        }
        .language-selector__flag {
          font-size: 16px;
        }
        .language-selector__arrow {
          font-size: 10px;
          transition: transform 0.2s;
        }
        .language-selector__dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          margin-top: 4px;
          background: white;
          border: 1px solid #ddd;
          border-radius: 6px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          list-style: none;
          padding: 4px 0;
          z-index: 100;
          max-height: 200px;
          overflow-y: auto;
        }
        .language-selector__option {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 16px;
          cursor: pointer;
          transition: background 0.15s;
        }
        .language-selector__option:hover {
          background: #f8f9fa;
        }
        .language-selector__option.selected {
          background: #e8f5e9;
          color: #2e7d32;
          font-weight: 500;
        }
        .language-selector__option-native {
          font-size: 14px;
        }
        .language-selector__option-english {
          font-size: 12px;
          color: #666;
        }
      `}</style>
    </div>
  );
}

export default LanguageSelector;