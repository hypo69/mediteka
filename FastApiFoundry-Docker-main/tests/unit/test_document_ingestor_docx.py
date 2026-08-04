# -*- coding: utf-8 -*-
import pytest
import io
import zipfile
import os
import tempfile
from src.rag.document_ingestor import DocumentIngestor

def test_extract_docx_hyperlinks_modular():
    """Модульный тест для проверки извлечения гиперссылок из ZIP-структуры DOCX."""
    ingestor = DocumentIngestor(settings={})
    
    # 1. Создание mock DOCX (ZIP-архива) в памяти
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, 'w') as z:
        # Создаем карту отношений (ID -> URL)
        rels_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
            <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="http://gemini.google.com" TargetMode="External"/>
        </Relationships>"""
        z.writestr('word/_rels/document.xml.rels', rels_xml)
        
        # Создаем основной документ с гиперссылкой
        doc_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
            <w:body>
                <w:p>
                    <w:hyperlink r:id="rId1">
                        <w:r><w:t>Click Here</w:t></w:r>
                    </w:hyperlink>
                </w:p>
            </w:body>
        </w:document>"""
        z.writestr('word/document.xml', doc_xml)
    
    docx_io.seek(0)
    
    # 2. Сохранение во временный файл для теста
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(docx_io.read())
        temp_name = tf.name
    
    try:
        # 3. Вызов тестируемого метода
        links = ingestor._extract_docx_hyperlinks(temp_name)
        
        # 4. Проверка результата
        assert "Click Here: http://gemini.google.com" in links
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def test_extract_docx_hidden_text_modular():
    """Модульный тест для проверки извлечения скрытого текста из XML-фикстуры DOCX."""
    ingestor = DocumentIngestor(settings={})
    
    # 1. Создание mock DOCX в памяти
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, 'w') as z:
        # XML с обычным текстом и текстом под тегом w:vanish
        doc_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r><w:t>Visible text.</w:t></w:r>
                    <w:r>
                        <w:rPr><w:vanish/></w:rPr>
                        <w:t>Secret info.</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>"""
        z.writestr('word/document.xml', doc_xml)
    
    docx_io.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(docx_io.read())
        temp_name = tf.name
    
    try:
        # 2. Вызов метода (он должен вернуть только скрытый текст)
        hidden = ingestor._extract_docx_hidden_text(temp_name)
        assert "Secret info." in hidden
        assert "Visible text." not in hidden
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def test_extract_docx_hidden_text_modular():
    """Модульный тест для проверки извлечения скрытого текста из XML-фикстуры DOCX."""
    ingestor = DocumentIngestor(settings={})
    
    # 1. Создание mock DOCX в памяти
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, 'w') as z:
        # XML с обычным текстом и текстом под тегом w:vanish
        doc_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r><w:t>Visible text.</w:t></w:r>
                    <w:r>
                        <w:rPr><w:vanish/></w:rPr>
                        <w:t>Secret info.</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>"""
        z.writestr('word/document.xml', doc_xml)
    
    docx_io.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(docx_io.read())
        temp_name = tf.name
    
    try:
        # 2. Вызов метода (он должен вернуть только скрытый текст)
        hidden = ingestor._extract_docx_hidden_text(temp_name)
        assert "Secret info." in hidden
        assert "Visible text." not in hidden
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def test_extract_docx_custom_properties_modular():
    """Модульный тест для проверки извлечения пользовательских свойств из DOCX."""
    ingestor = DocumentIngestor(settings={})
    
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, 'w') as z:
        custom_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
                    xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
            <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="ProjectName">
                <vt:lpwstr>FastApiFoundry</vt:lpwstr>
            </property>
            <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="3" name="Version">
                <vt:lpwstr>1.0.0</vt:lpwstr>
            </property>
            <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="4" name="IsDraft">
                <vt:bool>true</vt:bool>
            </property>
        </Properties>"""
        z.writestr('docProps/custom.xml', custom_xml)
    
    docx_io.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tf.write(docx_io.read())
        temp_name = tf.name
    
    try:
        custom_props = ingestor._extract_docx_custom_properties(temp_name)
        assert custom_props == {
            "custom_ProjectName": "FastApiFoundry",
            "custom_Version": "1.0.0",
            "custom_IsDraft": "true" # lxml reads bool as string
        }
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)