# QNotebook - Jupyter-style Notebook for QGIS

## Overview

QNotebook is a QGIS plugin that brings Jupyter-style notebook functionality directly into QGIS Python Console. It allows you to create, edit, and execute code cells interactively while working with your GIS data.

## Features

- **Jupyter-style interface** integrated into QGIS Python Console
- **Multiple cell types**: Code, Markdown, and Raw
- **Shared namespace** between cells
- **Save/Load notebooks** in Jupyter .ipynb format
- **Export capabilities** to HTML and Python scripts
- **Code templates** for common GIS operations
- **QGIS variables** pre-loaded in namespace

## Interface Components

### Toolbar

| Button | Function | Shortcut |
|--------|----------|----------|
| 💾 | Save notebook | Ctrl+S |
| 📁 | Open notebook | Ctrl+O |
| 📤 | Export notebook | - |
| ➕ | Add new cell | B |
| ▶ | Run current cell | Shift+Enter |
| ⏩ | Run all cells | - |
| ⏹ | Stop execution | - |
| 🔄 | Restart kernel | - |
| 🧹 | Clear all outputs | - |

### Cell Operations

Each cell has:
- **Run button**: Execute the cell
- **Clear button**: Clear output
- **Delete button**: Remove cell
- **Cell number**: Shows execution order
