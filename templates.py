# -*- coding: utf-8 -*-
"""
QNotebook Templates - Predefined code templates
"""

NOTEBOOK_TEMPLATES = {
    "Layer Operations": {
        "Load Vector Layer": """# Load active layer
layer = iface.activeLayer()
if layer:
    print(f"Layer: {layer.name()}")
    print(f"Features: {layer.featureCount()}")
    print(f"CRS: {layer.crs().authid()}")
    print(f"Fields: {[field.name() for field in layer.fields()]}")
""",
        
        "Create Memory Layer": """# Create a new memory layer
vl = QgsVectorLayer("Point?crs=EPSG:4326&field=id:integer&field=name:string(50)", 
                     "temp_points", "memory")

# Add features
pr = vl.dataProvider()
vl.startEditing()

# Add a point
feat = QgsFeature()
feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10, 45)))
feat.setAttributes([1, "First Point"])
pr.addFeature(feat)

vl.commitChanges()
QgsProject.instance().addMapLayer(vl)
print(f"Created layer with {vl.featureCount()} features")
""",

        "Layer from CSV": """# Load CSV as layer
import os
csv_path = '/path/to/your.csv'  # Change this
uri = f"file:///{csv_path}?delimiter=,&xField=lon&yField=lat&crs=EPSG:4326"

csv_layer = QgsVectorLayer(uri, "CSV Layer", "delimitedtext")
if csv_layer.isValid():
    QgsProject.instance().addMapLayer(csv_layer)
    print(f"Loaded {csv_layer.featureCount()} features from CSV")
else:
    print("Failed to load CSV")
""",

        "Export to GeoPackage": """# Export layer to GeoPackage
layer = iface.activeLayer()
output_path = '/path/to/output.gpkg'  # Change this

options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = 'GPKG'
options.fileEncoding = 'UTF-8'

error = QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, output_path, QgsCoordinateTransformContext(), options
)

if error[0] == QgsVectorFileWriter.NoError:
    print(f"Successfully exported to {output_path}")
else:
    print(f"Export failed: {error[1]}")
"""
    },
    
    "Data Analysis": {
        "Feature Statistics": """# Calculate statistics for a field
layer = iface.activeLayer()
field_name = 'your_field_name'  # Change this

if layer and field_name in [f.name() for f in layer.fields()]:
    values = []
    for feature in layer.getFeatures():
        value = feature[field_name]
        if value is not None:
            values.append(float(value))
    
    if values:
        import statistics
        print(f"Count: {len(values)}")
        print(f"Min: {min(values):.2f}")
        print(f"Max: {max(values):.2f}")
        print(f"Mean: {statistics.mean(values):.2f}")
        print(f"Median: {statistics.median(values):.2f}")
        print(f"Std Dev: {statistics.stdev(values):.2f}" if len(values) > 1 else "")
""",

        "Spatial Analysis": """# Find features within distance
layer = iface.activeLayer()
search_distance = 1000  # meters

# Get selected feature as reference
selected = layer.selectedFeatures()
if selected:
    ref_feature = selected[0]
    ref_geom = ref_feature.geometry()
    
    nearby_features = []
    for feature in layer.getFeatures():
        if feature.id() != ref_feature.id():
            if ref_geom.distance(feature.geometry()) <= search_distance:
                nearby_features.append(feature)
    
    print(f"Found {len(nearby_features)} features within {search_distance}m")
    
    # Select nearby features
    layer.selectByIds([f.id() for f in nearby_features])
""",

        "Attribute Table Summary": """# Summarize attribute table
layer = iface.activeLayer()

if layer:
    # Get field types
    for field in layer.fields():
        print(f"{field.name()}: {field.typeName()}")
    
    print("\\n--- Unique Values ---")
    # Show unique values for string fields
    for field in layer.fields():
        if field.type() == QVariant.String:
            unique_values = layer.uniqueValues(layer.fields().indexOf(field.name()))
            print(f"{field.name()}: {len(unique_values)} unique values")
            if len(unique_values) <= 10:
                print(f"  Values: {list(unique_values)[:10]}")
"""
    },
    
    "Selection & Filtering": {
        "Select by Expression": """# Select features by expression
layer = iface.activeLayer()
expression = '"population" > 10000'  # Change this

layer.selectByExpression(expression)
selected_count = layer.selectedFeatureCount()
print(f"Selected {selected_count} features with: {expression}")

# Process selected features
for feature in layer.selectedFeatures():
    print(f"Feature {feature.id()}: {feature.attributes()}")
""",

        "Filter Layer": """# Apply filter to layer (temporary)
layer = iface.activeLayer()
filter_expression = '"category" = \\'residential\\''  # Change this

# Apply filter
layer.setSubsetString(filter_expression)
print(f"Filter applied: {filter_expression}")
print(f"Visible features: {layer.featureCount()}")

# To remove filter:
# layer.setSubsetString("")
""",

        "Select by Location": """# Select by location using another layer
target_layer = iface.activeLayer()
overlay_layer = QgsProject.instance().mapLayersByName('overlay_layer_name')[0]  # Change

# Select target features that intersect overlay
processing.run("native:selectbylocation", {
    'INPUT': target_layer,
    'PREDICATE': [0],  # 0=intersects
    'INTERSECT': overlay_layer,
    'METHOD': 0  # 0=new selection
})

print(f"Selected {target_layer.selectedFeatureCount()} features")
"""
    },
    
    "Symbology & Styling": {
        "Graduated Renderer": """# Create graduated color renderer
layer = iface.activeLayer()
field_name = 'population'  # Change this

# Create graduated renderer
ranges = []
colors = ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494']
min_val = 0
max_val = 100000
num_classes = 5
step = (max_val - min_val) / num_classes

for i in range(num_classes):
    lower = min_val + (i * step)
    upper = min_val + ((i + 1) * step)
    label = f"{int(lower)} - {int(upper)}"
    
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(QColor(colors[i]))
    
    range_item = QgsRendererRange(lower, upper, symbol, label)
    ranges.append(range_item)

renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
layer.setRenderer(renderer)
layer.triggerRepaint()
print(f"Applied graduated renderer with {num_classes} classes")
""",

        "Categorized Renderer": """# Create categorized renderer
layer = iface.activeLayer()
field_name = 'category'  # Change this

# Get unique values
unique_values = layer.uniqueValues(layer.fields().indexOf(field_name))

categories = []
for i, value in enumerate(unique_values):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    # Generate random color
    symbol.setColor(QColor.fromHsv((i * 360) // len(unique_values), 200, 200))
    
    category = QgsRendererCategory(value, symbol, str(value))
    categories.append(category)

from qgis.core import QgsCategorizedSymbolRenderer
renderer = QgsCategorizedSymbolRenderer(field_name, categories)
layer.setRenderer(renderer)
layer.triggerRepaint()
print(f"Applied categorized renderer with {len(categories)} categories")
""",

        "Label Features": """# Add labels to features
layer = iface.activeLayer()
field_name = 'name'  # Change this

# Create label settings
settings = QgsPalLayerSettings()
settings.fieldName = field_name
settings.enabled = True

# Create text format
text_format = QgsTextFormat()
text_format.setSize(10)
text_format.setColor(QColor('black'))
settings.setFormat(text_format)

# Apply labels
labeling = QgsVectorLayerSimpleLabeling(settings)
layer.setLabeling(labeling)
layer.setLabelsEnabled(True)
layer.triggerRepaint()
print(f"Labels enabled for field: {field_name}")
"""
    },
    
    "Processing": {
        "Buffer Features": """# Buffer selected features
import processing

layer = iface.activeLayer()
if layer and layer.selectedFeatureCount() > 0:
    result = processing.run("native:buffer", {
        'INPUT': QgsProcessingFeatureSourceDefinition(
            layer.id(), selectedFeaturesOnly=True
        ),
        'DISTANCE': 100,
        'SEGMENTS': 5,
        'OUTPUT': 'memory:'
    })
    
    buffer_layer = result['OUTPUT']
    buffer_layer.setName(f"{layer.name()}_buffer")
    QgsProject.instance().addMapLayer(buffer_layer)
    print(f"Buffer created with {buffer_layer.featureCount()} features")
""",

        "Dissolve": """# Dissolve features by attribute
import processing

layer = iface.activeLayer()
dissolve_field = 'region'  # Change this

result = processing.run("native:dissolve", {
    'INPUT': layer,
    'FIELD': [dissolve_field],
    'OUTPUT': 'memory:'
})

dissolved_layer = result['OUTPUT']
dissolved_layer.setName(f"{layer.name()}_dissolved")
QgsProject.instance().addMapLayer(dissolved_layer)
print(f"Dissolved to {dissolved_layer.featureCount()} features")
""",

        "Spatial Join": """# Join attributes by location
import processing

target_layer = iface.activeLayer()
join_layer = QgsProject.instance().mapLayersByName('join_layer_name')[0]  # Change

result = processing.run("native:joinattributesbylocation", {
    'INPUT': target_layer,
    'JOIN': join_layer,
    'PREDICATE': [0],  # intersects
    'JOIN_FIELDS': [],  # empty = all fields
    'METHOD': 0,  # one-to-many
    'OUTPUT': 'memory:'
})

joined_layer = result['OUTPUT']
joined_layer.setName(f"{target_layer.name()}_joined")
QgsProject.instance().addMapLayer(joined_layer)
print(f"Spatial join completed: {joined_layer.featureCount()} features")
"""
    },
    
    "Visualization": {
        "Matplotlib Chart": """import matplotlib.pyplot as plt

# Create bar chart from layer attributes
layer = iface.activeLayer()
field_name = 'category'  # Change this

# Count features by category
categories = {}
for feature in layer.getFeatures():
    cat = feature[field_name]
    categories[cat] = categories.get(cat, 0) + 1

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(categories.keys(), categories.values())
ax.set_xlabel(field_name)
ax.set_ylabel('Count')
ax.set_title(f'{layer.name()} - Distribution by {field_name}')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
""",

        "Feature Histogram": """import matplotlib.pyplot as plt

# Create histogram from numeric field
layer = iface.activeLayer()
field_name = 'population'  # Change this

values = []
for feature in layer.getFeatures():
    value = feature[field_name]
    if value is not None:
        values.append(float(value))

if values:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(values, bins=20, edgecolor='black')
    ax.set_xlabel(field_name)
    ax.set_ylabel('Frequency')
    ax.set_title(f'{layer.name()} - {field_name} Distribution')
    
    # Add statistics
    ax.axvline(sum(values)/len(values), color='red', 
               linestyle='dashed', linewidth=1, label='Mean')
    ax.legend()
    
    plt.tight_layout()
    plt.show()
"""
    },
    
    "Raster Operations": {
        "Raster Statistics": """# Get raster layer statistics
layer = iface.activeLayer()

if layer and layer.type() == QgsMapLayer.RasterLayer:
    extent = layer.extent()
    print(f"Raster: {layer.name()}")
    print(f"Bands: {layer.bandCount()}")
    print(f"Width: {layer.width()} pixels")
    print(f"Height: {layer.height()} pixels")
    print(f"Extent: {extent.toString()}")
    
    # Get band statistics
    for band in range(1, layer.bandCount() + 1):
        stats = layer.dataProvider().bandStatistics(band)
        print(f"\\nBand {band}:")
        print(f"  Min: {stats.minimumValue:.2f}")
        print(f"  Max: {stats.maximumValue:.2f}")
        print(f"  Mean: {stats.mean:.2f}")
""",

        "Sample Raster Values": """# Sample raster values at points
raster_layer = iface.activeLayer()
point_layer = QgsProject.instance().mapLayersByName('points')[0]  # Change

if raster_layer.type() == QgsMapLayer.RasterLayer:
    for feature in point_layer.getFeatures():
        point = feature.geometry().asPoint()
        value, success = raster_layer.dataProvider().sample(
            QgsPointXY(point), 1  # band 1
        )
        if success:
            print(f"Point {feature.id()}: Value = {value}")
"""
    }
}