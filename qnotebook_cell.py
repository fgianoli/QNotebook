# -*- coding: utf-8 -*-
"""
QNotebook Cell - Single notebook cell implementation
"""

import sys
import traceback
from io import StringIO

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFrame
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont

from qgis.gui import QgsCodeEditorPython

class QNotebookCell(QFrame):
    """Single notebook cell."""
    
    executed = pyqtSignal(object)
    deleted = pyqtSignal(object)
    selected = pyqtSignal(object)
    
    def __init__(self, shell=None, cell_type='code', iface=None, parent=None, shared_namespace=None):
        super().__init__(parent)
        self.shell = shell
        self.cell_type = cell_type
        self.iface = iface
        self.execution_count = 0
        self.outputs = []
        
        # Usa namespace condiviso se fornito, altrimenti creane uno
        self.shared_namespace = shared_namespace if shared_namespace is not None else self.create_default_namespace()
        
        self.setup_ui()
    
    def create_default_namespace(self):
        """Crea un namespace di default con le variabili QGIS."""
        from qgis.core import (
            Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer,
            QgsFeature, QgsGeometry, QgsPointXY, QgsField,
            QgsVectorFileWriter, QgsCoordinateTransformContext,
            QgsMapSettings, QgsSymbol, QgsSimpleMarkerSymbolLayer,
            QgsGraduatedSymbolRenderer, QgsRendererRange,
            QgsClassificationRange, QgsStyle, QgsColorRamp,
            QgsGradientColorRamp, QgsApplication, QgsProcessingFeedback,
            QgsCoordinateReferenceSystem, QgsRectangle, QgsExpression,
            QgsExpressionContext, QgsExpressionContextUtils
        )
        from qgis.PyQt.QtCore import QVariant
        from qgis.PyQt.QtGui import QColor
        
        try:
            from qgis.utils import iface
        except:
            iface = self.iface
        
        namespace = {
            '__name__': '__main__',
            '__builtins__': __builtins__,
            'iface': iface,
            'Qgis': Qgis,
            'QgsProject': QgsProject,
            'QgsVectorLayer': QgsVectorLayer,
            'QgsRasterLayer': QgsRasterLayer,
            'QgsFeature': QgsFeature,
            'QgsGeometry': QgsGeometry,
            'QgsPointXY': QgsPointXY,
            'QgsField': QgsField,
            'QVariant': QVariant,
            'QgsVectorFileWriter': QgsVectorFileWriter,
            'QgsCoordinateTransformContext': QgsCoordinateTransformContext,
            'QgsMapSettings': QgsMapSettings,
            'QgsSymbol': QgsSymbol,
            'QgsSimpleMarkerSymbolLayer': QgsSimpleMarkerSymbolLayer,
            'QgsGraduatedSymbolRenderer': QgsGraduatedSymbolRenderer,
            'QgsRendererRange': QgsRendererRange,
            'QgsClassificationRange': QgsClassificationRange,
            'QgsStyle': QgsStyle,
            'QgsColorRamp': QgsColorRamp,
            'QgsGradientColorRamp': QgsGradientColorRamp,
            'QgsApplication': QgsApplication,
            'QgsProcessingFeedback': QgsProcessingFeedback,
            'QgsCoordinateReferenceSystem': QgsCoordinateReferenceSystem,
            'QgsRectangle': QgsRectangle,
            'QgsExpression': QgsExpression,
            'QgsExpressionContext': QgsExpressionContext,
            'QgsExpressionContextUtils': QgsExpressionContextUtils,
            'QColor': QColor,
            'canvas': iface.mapCanvas() if iface else None,
            'project': QgsProject.instance(),
        }
        
        # Aggiungi moduli comuni se disponibili
        try:
            import processing
            namespace['processing'] = processing
        except:
            pass
        
        try:
            import numpy as np
            namespace['np'] = np
        except:
            pass
        
        try:
            import pandas as pd
            namespace['pd'] = pd
        except:
            pass
        
        try:
            import matplotlib.pyplot as plt
            namespace['plt'] = plt
        except:
            pass
        
        try:
            import statistics
            namespace['statistics'] = statistics
        except:
            pass
        
        return namespace
    
    def setup_ui(self):
        """Setup cell UI."""
        self.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout()
        
        # Cell number (solo per celle code)
        self.number_label = QLabel("[]: ")
        self.number_label.setMinimumWidth(50)
        layout.addWidget(self.number_label)
        
        # Main content area
        content_layout = QVBoxLayout()
        
        # Code editor
        self.editor = QgsCodeEditorPython()
        self.editor.setMinimumHeight(60)
        content_layout.addWidget(self.editor)
        
        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(200)
        self.output.setVisible(False)
        content_layout.addWidget(self.output)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.clicked.connect(self.run_cell)
        button_layout.addWidget(self.run_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_cell)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        content_layout.addLayout(button_layout)
        
        layout.addLayout(content_layout)
        self.setLayout(layout)
        
        # Aggiorna UI in base al tipo di cella
        self.update_cell_type_ui()
    
    def update_cell_type_ui(self):
        """Aggiorna l'interfaccia in base al tipo di cella."""
        if self.cell_type == 'markdown':
            self.number_label.setText("    ")
            self.run_btn.setText("▶ Render")
        elif self.cell_type == 'raw':
            self.number_label.setText("    ")
            self.run_btn.setEnabled(False)
        else:  # code
            self.number_label.setText(f"[{self.execution_count if self.execution_count else ''}]: ")
            self.run_btn.setText("▶ Run")
            self.run_btn.setEnabled(True)
    
    def run_cell(self, advance=True):
        """Execute the cell based on its type."""
        if self.cell_type == 'markdown':
            self.render_markdown()
        elif self.cell_type == 'raw':
            # Le celle raw non vengono eseguite
            pass
        else:  # code
            self.execute_code(advance)
    
    def render_markdown(self):
        """Render markdown content."""
        markdown_text = self.editor.text()
        if not markdown_text.strip():
            return
        
        # Clear previous output
        self.clear_output()
        self.output.setVisible(True)
        
        # Render semplice del markdown (converti in HTML base)
        html = self.simple_markdown_to_html(markdown_text)
        self.output.setHtml(html)
    
    def simple_markdown_to_html(self, text):
        """Conversione semplice da markdown a HTML."""
        html = text
        
        # Headers
        html = html.replace('### ', '<h3>')
        html = html.replace('## ', '<h2>')
        html = html.replace('# ', '<h1>')
        
        # Bold e italic
        import re
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Line breaks
        html = html.replace('\n', '<br>')
        
        # Lists
        lines = html.split('<br>')
        for i, line in enumerate(lines):
            if line.strip().startswith('- '):
                lines[i] = '<li>' + line.strip()[2:] + '</li>'
        html = '<br>'.join(lines)
        
        # Wrap in div
        html = f'<div style="padding: 10px; font-family: Arial, sans-serif;">{html}</div>'
        
        return html
    
    def get_execution_namespace(self):
        """Ottieni il namespace per l'esecuzione del codice."""
        # Se abbiamo accesso alla shell della console, usa il suo namespace
        if self.shell and hasattr(self.shell, 'locals'):
            return self.shell.locals
        
        # Altrimenti usa il namespace condiviso
        return self.shared_namespace
    
    def execute_code(self, advance=True):
        """Execute Python code."""
        code = self.editor.text()
        if not code.strip():
            return
        
        self.execution_count += 1
        self.number_label.setText(f"[{self.execution_count}]: ")
        
        # Clear previous output
        self.clear_output()
        self.output.setVisible(True)
        
        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # Ottieni il namespace per l'esecuzione
            exec_namespace = self.get_execution_namespace()
            
            # Esegui il codice nel namespace condiviso
            exec(code, exec_namespace)
            
            # Get output
            output = stdout_capture.getvalue()
            if output:
                self.output.append(output)
                
        except Exception as e:
            error = traceback.format_exc()
            self.output.append(f"<span style='color: red;'>{error}</span>")
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        if advance:
            self.executed.emit(self)
    
    def clear_output(self):
        """Clear the output area."""
        self.output.clear()
        if not self.output.toPlainText():
            self.output.setVisible(False)
    
    def delete_cell(self):
        """Delete this cell."""
        self.deleted.emit(self)
    
    def set_selected(self, selected):
        """Set cell selection state."""
        if selected:
            self.setStyleSheet("QFrame { border: 2px solid #4CAF50; }")
            self.selected.emit(self)
        else:
            self.setStyleSheet("")
    
    def set_code(self, code):
        """Set cell code."""
        self.editor.setText(code)
    
    def change_type(self, cell_type):
        """Change cell type."""
        self.cell_type = cell_type.lower()
        self.update_cell_type_ui()
    
    def to_dict(self):
        """Convert cell to dictionary."""
        # Salva source come lista di stringhe (formato Jupyter standard)
        source_text = self.editor.text()
        source_lines = source_text.split('\n') if source_text else []
        
        return {
            'cell_type': self.cell_type,
            'source': source_lines,
            'execution_count': self.execution_count if self.cell_type == 'code' else None,
            'outputs': self.outputs,
            'metadata': {}
        }
    
    def from_dict(self, data):
        """Load cell from dictionary."""
        self.cell_type = data.get('cell_type', 'code')
        
        # Gestisci source come lista o stringa
        source = data.get('source', '')
        if isinstance(source, list):
            # Jupyter format: lista di stringhe
            source = ''.join(source)
        elif source is None:
            source = ''
        
        self.editor.setText(source)
        
        # Gestisci execution_count (solo per celle code)
        if self.cell_type == 'code':
            exec_count = data.get('execution_count')
            if exec_count is None:
                exec_count = data.get('metadata', {}).get('execution_count', 0)
            self.execution_count = exec_count if exec_count else 0
        else:
            self.execution_count = 0
        
        # Aggiorna UI in base al tipo
        self.update_cell_type_ui()
        
        # Carica outputs se presenti
        self.outputs = data.get('outputs', [])
        if self.outputs:
            # Mostra gli output salvati
            self.output.setVisible(True)
            for output_data in self.outputs:
                if output_data.get('output_type') == 'stream':
                    text = output_data.get('text', '')
                    if isinstance(text, list):
                        text = ''.join(text)
                    self.output.append(text)
                elif output_data.get('output_type') == 'error':
                    error_text = '\n'.join(output_data.get('traceback', []))
                    self.output.append(f"<span style='color: red;'>{error_text}</span>")