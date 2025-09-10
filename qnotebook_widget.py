# -*- coding: utf-8 -*-
"""
QNotebook Widget - Main notebook interface
"""

import os
import sys
import json
import datetime
from pathlib import Path

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QScrollArea, QLabel, QPushButton, QFileDialog,
    QMenu, QToolButton, QComboBox, QAction,
    QMessageBox, QShortcut, QApplication
)
from qgis.PyQt.QtCore import (
    Qt, QSize, QTimer, pyqtSignal,
    QPropertyAnimation, QEasingCurve
)
from qgis.PyQt.QtGui import (
    QIcon, QKeySequence, QFont
)

from qgis.core import QgsProject, Qgis
from qgis.gui import QgsMessageBar

# Import cell class
from .qnotebook_cell import QNotebookCell

# Templates
from .templates import NOTEBOOK_TEMPLATES

class QNotebookWidget(QWidget):
    """Main notebook widget for QGIS."""
    
    def __init__(self, iface, console=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.console = console
        self.cells = []
        self.current_cell = None
        self.execution_count = 0
        
        # Inizializza il namespace condiviso con le variabili QGIS
        self.shared_namespace = self.initialize_shared_namespace()
        
        self.setup_ui()
        self.setup_shortcuts()
        self.load_stylesheet()
    
    def initialize_shared_namespace(self):
        """Inizializza il namespace condiviso con tutte le variabili QGIS necessarie."""
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
        
        # Prova a ottenere iface
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
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Toolbar
        self.create_toolbar(main_layout)
        
        # Notebook area
        self.create_notebook_area(main_layout)
        
        # Status bar
        self.create_status_bar(main_layout)
        
        # Add first cell
        self.add_cell()
    
    def create_toolbar(self, layout):
        """Create main toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        
        # File operations
        self.toolbar.addAction("💾", self.save_notebook).setToolTip("Save (Ctrl+S)")
        self.toolbar.addAction("📁", self.load_notebook).setToolTip("Open (Ctrl+O)")
        self.toolbar.addAction("📤", self.export_notebook).setToolTip("Export")
        
        self.toolbar.addSeparator()
        
        # Cell operations
        self.toolbar.addAction("➕", self.add_cell).setToolTip("Add Cell (B)")
        self.toolbar.addAction("▶", self.run_current_cell).setToolTip("Run (Shift+Enter)")
        self.toolbar.addAction("⏩", self.run_all_cells).setToolTip("Run All")
        self.toolbar.addAction("⏹", self.interrupt_execution).setToolTip("Stop")
        self.toolbar.addAction("🔄", self.restart_kernel).setToolTip("Restart")
        
        self.toolbar.addSeparator()
        
        # Cell type
        self.cell_type_combo = QComboBox()
        self.cell_type_combo.addItems(["Code", "Markdown", "Raw"])
        self.cell_type_combo.currentTextChanged.connect(self.change_cell_type)
        self.toolbar.addWidget(self.cell_type_combo)
        
        self.toolbar.addSeparator()
        
        # Clear
        self.toolbar.addAction("🧹", self.clear_all_outputs).setToolTip("Clear All Outputs")
        
        self.toolbar.addSeparator()
        
        # Templates
        self.create_templates_menu()
        
        layout.addWidget(self.toolbar)
    
    def create_templates_menu(self):
        """Create templates menu button."""
        templates_btn = QToolButton()
        templates_btn.setText("📝 Templates")
        templates_btn.setPopupMode(QToolButton.InstantPopup)
        
        templates_menu = QMenu()
        
        # Add template actions
        for category, templates in NOTEBOOK_TEMPLATES.items():
            category_menu = templates_menu.addMenu(category)
            for name, code in templates.items():
                action = category_menu.addAction(name)
                action.triggered.connect(lambda checked, c=code: self.insert_template(c))
        
        templates_btn.setMenu(templates_menu)
        self.toolbar.addWidget(templates_btn)
    
    def create_notebook_area(self, layout):
        """Create scrollable notebook area."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.cells_container = QWidget()
        self.cells_layout = QVBoxLayout()
        self.cells_layout.setSpacing(8)
        self.cells_layout.setContentsMargins(10, 10, 10, 10)
        self.cells_container.setLayout(self.cells_layout)
        
        self.scroll_area.setWidget(self.cells_container)
        layout.addWidget(self.scroll_area)
    
    def create_status_bar(self, layout):
        """Create status bar."""
        status_widget = QWidget()
        status_widget.setMaximumHeight(30)
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # Kernel status
        self.kernel_status = QLabel("⚪ Ready")
        self.kernel_status.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # Cell count
        self.cell_count_label = QLabel("Cells: 1")
        
        status_layout.addWidget(self.kernel_status)
        status_layout.addStretch()
        status_layout.addWidget(self.cell_count_label)
        
        status_widget.setLayout(status_layout)
        layout.addWidget(status_widget)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        shortcuts = {
            "Ctrl+S": self.save_notebook,
            "Ctrl+O": self.load_notebook,
            "Shift+Return": self.run_current_cell,
            "Ctrl+Return": lambda: self.run_current_cell(advance=False),
            "B": self.add_cell,
            "A": self.add_cell_above,
            "D, D": self.delete_current_cell,
        }
        
        for key, func in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(func)
    
    def load_stylesheet(self):
        """Load custom stylesheet."""
        style = """
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        
        QToolBar {
            background: linear-gradient(to bottom, #f7f7f7, #efefef);
            border-bottom: 1px solid #d0d0d0;
            padding: 5px;
            spacing: 3px;
        }
        
        QScrollArea {
            border: none;
            background-color: #fafafa;
        }
        """
        self.setStyleSheet(style)
    
    def add_cell(self, cell_type='code', position=None):
        """Add a new cell to the notebook."""
        # Get console shell
        shell = self.get_console_shell()
        
        # Create cell con namespace condiviso
        cell = QNotebookCell(
            shell=shell,
            cell_type=cell_type,
            iface=self.iface,
            parent=self,
            shared_namespace=self.shared_namespace  # Passa il namespace condiviso già inizializzato
        )
        
        # Connect signals
        cell.executed.connect(self.on_cell_executed)
        cell.deleted.connect(self.on_cell_deleted)
        cell.selected.connect(self.on_cell_selected)
        
        # Add to layout
        if position is None:
            self.cells.append(cell)
            self.cells_layout.addWidget(cell)
        else:
            self.cells.insert(position, cell)
            self.cells_layout.insertWidget(position, cell)
        
        # Update UI
        self.update_cell_count()
        cell.set_selected(True)
        
        return cell
    
    def get_console_shell(self):
        """Get the Python console shell."""
        if self.console:
            if hasattr(self.console, 'shell'):
                return self.console.shell
            elif hasattr(self.console, 'console') and hasattr(self.console.console, 'shell'):
                return self.console.console.shell
        return None
    
    def on_cell_executed(self, cell):
        """Handle cell execution."""
        self.execution_count += 1
        
        # Auto advance to next cell
        idx = self.cells.index(cell)
        if idx < len(self.cells) - 1:
            self.cells[idx + 1].set_selected(True)
        else:
            # Add new cell at end
            self.add_cell()
    
    def on_cell_deleted(self, cell):
        """Handle cell deletion."""
        if cell in self.cells:
            self.cells.remove(cell)
            cell.deleteLater()
            self.update_cell_count()
    
    def on_cell_selected(self, cell):
        """Handle cell selection."""
        self.current_cell = cell
        
        # Update cell type combo
        if cell.cell_type:
            self.cell_type_combo.setCurrentText(cell.cell_type.capitalize())
    
    def update_cell_count(self):
        """Update cell count label."""
        self.cell_count_label.setText(f"Cells: {len(self.cells)}")
    
    def run_current_cell(self, advance=True):
        """Run the currently selected cell."""
        if self.current_cell:
            self.set_kernel_busy(True)
            self.current_cell.run_cell(advance)
            QTimer.singleShot(500, lambda: self.set_kernel_busy(False))
    
    def run_all_cells(self):
        """Run all cells in order."""
        self.set_kernel_busy(True)
        
        for cell in self.cells:
            cell.run_cell(advance=False)
            QApplication.processEvents()
        
        self.set_kernel_busy(False)
    
    def set_kernel_busy(self, busy):
        """Update kernel status indicator."""
        if busy:
            self.kernel_status.setText("⚡ Running")
            self.kernel_status.setStyleSheet("""
                QLabel {
                    background-color: #FFA726;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        else:
            self.kernel_status.setText("⚪ Ready")
            self.kernel_status.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
    
    def clear_all_outputs(self):
        """Clear all cell outputs."""
        reply = QMessageBox.question(
            self, 'Clear All Outputs',
            'Clear all cell outputs?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for cell in self.cells:
                cell.clear_output()
    
    def save_notebook(self):
        """Save notebook to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Notebook",
            os.path.expanduser("~/qgis_notebook.ipynb"),
            "Jupyter Notebook (*.ipynb);;JSON (*.json)"
        )
        
        if filename:
            try:
                notebook_data = self.to_notebook_format()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(notebook_data, f, indent=2)
                
                self.show_message(f"Notebook saved: {os.path.basename(filename)}", Qgis.Success)
            except Exception as e:
                self.show_message(f"Error saving: {str(e)}", Qgis.Critical)
    
    def load_notebook(self):
        """Load notebook from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Notebook",
            os.path.expanduser("~"),
            "Jupyter Notebook (*.ipynb);;JSON (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    notebook_data = json.load(f)
                
                self.from_notebook_format(notebook_data)
                self.show_message(f"Loaded: {os.path.basename(filename)}", Qgis.Success)
            except Exception as e:
                self.show_message(f"Error loading: {str(e)}", Qgis.Critical)
    
    def export_notebook(self):
        """Export notebook."""
        filename, filter_type = QFileDialog.getSaveFileName(
            self, "Export Notebook",
            os.path.expanduser("~/notebook_export.html"),
            "HTML (*.html);;Python Script (*.py)"
        )
        
        if filename:
            try:
                if "HTML" in filter_type:
                    self.export_as_html(filename)
                else:
                    self.export_as_python(filename)
                self.show_message(f"Exported: {os.path.basename(filename)}", Qgis.Success)
            except Exception as e:
                self.show_message(f"Error exporting: {str(e)}", Qgis.Critical)
    
    def to_notebook_format(self):
        """Convert to Jupyter notebook format."""
        cells = []
        for cell in self.cells:
            cell_dict = cell.to_dict()
            if 'metadata' not in cell_dict:
                cell_dict['metadata'] = {}
            if 'outputs' not in cell_dict:
                cell_dict['outputs'] = []
            cells.append(cell_dict)
        
        return {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "QGIS Python",
                    "language": "python",
                    "name": "qgis_python"
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": sys.version.split()[0]
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
    
    def from_notebook_format(self, notebook_data):
        """Load from Jupyter notebook format."""
        # Clear existing cells
        for cell in self.cells:
            cell.deleteLater()
        self.cells.clear()
        
        # Clear layout
        while self.cells_layout.count():
            item = self.cells_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load cells
        for cell_data in notebook_data.get('cells', []):
            cell = self.add_cell(cell_type=cell_data.get('cell_type', 'code'))
            cell.from_dict(cell_data)
    
    def show_message(self, message, level=Qgis.Info):
        """Show message in QGIS message bar."""
        self.iface.messageBar().pushMessage("QNotebook", message, level=level, duration=3)
    
    def insert_template(self, code):
        """Insert template code in current cell."""
        if self.current_cell:
            self.current_cell.set_code(code)
    
    def interrupt_execution(self):
        """Interrupt current execution (placeholder)."""
        # Nota: L'interruzione vera richiederebbe thread separati
        self.set_kernel_busy(False)
        self.show_message("Execution stopped", Qgis.Warning)
    
    def restart_kernel(self):
        """Restart Python kernel (clear namespace)."""
        reply = QMessageBox.question(
            self, 'Restart Kernel',
            'Restart kernel and clear all variables?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reinizializza il namespace condiviso
            self.shared_namespace = self.initialize_shared_namespace()
            
            # Reset execution count
            self.execution_count = 0
            for cell in self.cells:
                cell.execution_count = 0
                cell.number_label.setText("[]: ")
                cell.clear_output()
            
            self.show_message("Kernel restarted", Qgis.Info)
    
    def add_cell_above(self):
        """Add cell above current."""
        if self.current_cell and self.current_cell in self.cells:
            idx = self.cells.index(self.current_cell)
            self.add_cell(position=idx)
    
    def delete_current_cell(self):
        """Delete current cell."""
        if self.current_cell and len(self.cells) > 1:
            self.current_cell.delete_cell()
    
    def change_cell_type(self, cell_type):
        """Change current cell type."""
        if self.current_cell:
            self.current_cell.change_type(cell_type.lower())
    
    def export_as_html(self, filename):
        """Export notebook as HTML."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>QGIS Notebook Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .cell { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }
        .code { background: #f5f5f5; padding: 10px; font-family: monospace; }
        .output { background: white; padding: 10px; border-top: 1px solid #ddd; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>QGIS Notebook Export</h1>
"""
        
        for i, cell in enumerate(self.cells):
            html += f'<div class="cell">'
            html += f'<div class="code">In [{cell.execution_count}]:<br>'
            html += f'<pre>{cell.editor.text()}</pre></div>'
            
            output_text = cell.output.toPlainText()
            if output_text:
                html += f'<div class="output"><pre>{output_text}</pre></div>'
            
            html += '</div>'
        
        html += "</body></html>"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def export_as_python(self, filename):
        """Export as Python script."""
        code = "#!/usr/bin/env python\n"
        code += "# -*- coding: utf-8 -*-\n"
        code += "# QGIS Notebook Export\n\n"
        
        for i, cell in enumerate(self.cells):
            if cell.cell_type == 'code':
                code += f"# Cell {i+1}\n"
                code += cell.editor.text()
                code += "\n\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)