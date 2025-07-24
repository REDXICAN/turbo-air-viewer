import pandas as pd
import sqlite3
from datetime import datetime
import re
import os

# Check existing files
print("Checking for existing files:")
files_to_check = ['turbo_air_products.xlsx', 'turbo_air_db_online.sqlite']
for file in files_to_check:
    if os.path.exists(file):
        print(f"✓ Found: {file} ({os.path.getsize(file)} bytes)")
    else:
        print(f"✗ Not found: {file}")
print("-" * 50)

# Function to convert dimensions from inches to centimeters
def convert_dimensions_to_metric(dimensions_str):
    if pd.isna(dimensions_str) or dimensions_str == 'N/A':
        return 'N/A'
    
    # Extract numbers from the string
    numbers = re.findall(r'(\d+\.?\d*)', dimensions_str)
    
    if len(numbers) >= 3:
        # Convert inches to centimeters (1 inch = 2.54 cm)
        width_cm = float(numbers[0]) * 2.54
        depth_cm = float(numbers[1]) * 2.54
        height_cm = float(numbers[2]) * 2.54
        
        return f"{width_cm:.1f} cm W x {depth_cm:.1f} cm D x {height_cm:.1f} cm H"
    return dimensions_str

# Function to convert weight from pounds to kilograms
def convert_weight_to_metric(weight_str):
    if pd.isna(weight_str) or weight_str == 'N/A':
        return 'N/A'
    
    # Extract number from the string
    match = re.search(r'(\d+\.?\d*)', weight_str)
    
    if match:
        # Convert pounds to kilograms (1 pound = 0.453592 kg)
        weight_kg = float(match.group(1)) * 0.453592
        return f"{weight_kg:.1f} kg"
    return weight_str

# Create list of all products with complete specifications including new research
products = [
    # PRO Series (6 SKUs with complete data)
    {
        'SKU': 'PRO-12R-N(-L)',
        'Product Type': 'Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '17.75" W x 27.25" D x 78" H',
        'Weight': '336 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4+ HP, Top Mounted',
        'Capacity': '9.6 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$5,846.40',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Compact commercial reach-in refrigerator ideal for small kitchens, bars, and cafes. Features Turbo Air\'s patented self-cleaning condenser system.',
        'Use Cases': 'Small restaurants, Cafes, Bars, Food trucks, Catering operations'
    },
    {
        'SKU': 'PRO-15R-N(-L)',
        'Product Type': 'Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '17.75" W x 38.5" D x 78" H',
        'Weight': '340 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4+ HP, Top Mounted',
        'Capacity': '13.77 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,061.16',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Narrow footprint reach-in refrigerator with extra depth for maximum storage in tight spaces. Premium PRO series construction.',
        'Use Cases': 'Narrow kitchen spaces, Deli counters, Sandwich shops, Pizza restaurants'
    },
    {
        'SKU': 'PRO-26R-N(-L)',
        'Product Type': 'Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '3.1A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 33.875" D x 83" H',
        'Weight': '336 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/3 HP, Top Mounted',
        'Capacity': '25 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,712.92',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Premium single-door reach-in refrigerator with 25 cubic feet of storage. Industry-leading 7-year compressor warranty.',
        'Use Cases': 'Full-service restaurants, Institutional kitchens, Hotels, Hospitals'
    },
    {
        'SKU': 'PRO-26-2R-N(-L)',
        'Product Type': 'Reach-In Refrigerator (Half Door)',
        'Voltage': '115V',
        'Amperage': '3.1A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 33.875" D x 82.875" H',
        'Weight': '336 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/3 HP, Top Mounted',
        'Capacity': '24.8 cu. ft.',
        'Doors': '2 (Half Doors)',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,953.82',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation, Half doors reduce cold air loss',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Half-door design minimizes cold air loss while providing easy access to frequently used items. Ideal for high-traffic kitchens.',
        'Use Cases': 'Busy restaurant kitchens, Prep stations, Bakeries, Delis'
    },
    {
        'SKU': 'PRO-50R-N',
        'Product Type': 'Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '4A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '51.75" W x 33.875" D x 83" H',
        'Weight': '491 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '2/3 HP, Top Mounted',
        'Capacity': '43.4 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$8,931.88',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Two-section reach-in refrigerator offering maximum storage capacity with premium PRO series features and reliability.',
        'Use Cases': 'Large restaurants, Commercial kitchens, Institutional foodservice, Catering operations'
    },
    {
        'SKU': 'PRO-77-6R-N',
        'Product Type': 'Reach-In Refrigerator (Three Section Half Door)',
        'Voltage': '115V',
        'Amperage': '5.25A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '77.75" W x 33.875" D x 82.875" H',
        'Weight': '655 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1 HP, Top Mounted',
        'Capacity': '66.2 cu. ft.',
        'Doors': '6 (Half Doors)',
        'Shelves': '9',
        'Temperature Range': '33°F to 38°F',
        'Price': '$12,509.26',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Lifetime guaranteed door hinges & handles, Field reversible doors, USB temperature data download, Anti-corrosion coated evaporator, High-density polyurethane insulation, Half doors reduce cold air loss',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Three-section refrigerator with six half doors for maximum organization and minimal cold air loss. Top-of-the-line commercial refrigeration.',
        'Use Cases': 'High-volume restaurants, Central kitchens, Hotels, Convention centers'
    },

    # TSR Series (8 SKUs with complete data)
    {
        'SKU': 'TSR-23SD-N6(-L)',
        'Product Type': 'Solid Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '1.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27" W x 30.375" D x 83.25" H',
        'Weight': '274 lbs',
        'Refrigerant': 'R-600a',
        'Compressor': '1/8 HP (bottom-mounted)',
        'Capacity': '19.3 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$3,728.65',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation, Energy-efficient design',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Energy-efficient Super Deluxe refrigerator with R-600a refrigerant. Bottom-mounted compressor for easy service access.',
        'Use Cases': 'Restaurants, Cafes, Delis, Healthcare facilities'
    },
    {
        'SKU': 'TSR-35SD-N6',
        'Product Type': 'Solid Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.8A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '39.5" W x 30.375" D x 84.375" H',
        'Weight': '375 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP (bottom-mounted)',
        'Capacity': '29 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$4,933.19',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Two-door Super Deluxe refrigerator with advanced features and bottom-mounted compressor for improved ergonomics.',
        'Use Cases': 'Commercial kitchens, Restaurants, Institutional foodservice'
    },
    {
        'SKU': 'TSR-49SD-N6',
        'Product Type': 'Solid Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.3A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '54.375" W x 30.375" D x 84.25" H',
        'Weight': '427 lbs',
        'Refrigerant': 'R-600a',
        'Compressor': '1/5 HP (bottom-mounted)',
        'Capacity': '41.1 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$5,285.03',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation, Energy-efficient design',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Large capacity two-door refrigerator with energy-efficient R-600a refrigerant and Super Deluxe features.',
        'Use Cases': 'Large restaurants, Banquet facilities, Schools, Hospitals'
    },
    {
        'SKU': 'TSR-72SD-N',
        'Product Type': 'Solid Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '5.7A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '81.875" W x 30.375" D x 84.25" H',
        'Weight': '602 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/2 HP (bottom-mounted)',
        'Capacity': '64.1 cu. ft.',
        'Doors': '3',
        'Shelves': '9',
        'Temperature Range': '33°F to 38°F',
        'Price': '$7,137.21',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Three-door reach-in refrigerator with maximum storage capacity. Super Deluxe series reliability and features.',
        'Use Cases': 'High-volume kitchens, Central commissaries, Large institutions'
    },
    {
        'SKU': 'TSR-23GSD-N6',
        'Product Type': 'Glass Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '1.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27" W x 31.875" D x 83.25" H',
        'Weight': '310 lbs',
        'Refrigerant': 'R-600a',
        'Compressor': '1/5 HP (bottom-mounted)',
        'Capacity': '20 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$4,436.43',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Triple pane heated glass door, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Glass door merchandiser refrigerator perfect for display applications. Energy-efficient with heated glass to prevent condensation.',
        'Use Cases': 'Convenience stores, Delis, Grab-and-go displays, Cafeterias'
    },
    {
        'SKU': 'TSR-35GSD-N',
        'Product Type': 'Glass Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '3.1A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '39.5" W x 31.875" D x 83.25" H',
        'Weight': '400 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/3 HP (bottom-mounted)',
        'Capacity': '29.19 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,220.27',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Triple pane heated glass doors, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Two-door glass merchandiser with excellent product visibility and energy-efficient LED lighting.',
        'Use Cases': 'Retail foodservice, Cafeterias, Beverage display, Grab-and-go'
    },
    {
        'SKU': 'TSR-49GSD-N',
        'Product Type': 'Glass Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '3.1A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '54.375" W x 31.875" D x 83.25" H',
        'Weight': '480 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/3 HP (bottom-mounted)',
        'Capacity': '44.14 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,518.32',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Triple pane heated glass doors, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Large capacity glass door refrigerator ideal for maximum product visibility and merchandising.',
        'Use Cases': 'Supermarkets, C-stores, Cafeterias, Display merchandising'
    },
    {
        'SKU': 'TSR-72GSD-N',
        'Product Type': 'Glass Door Reach-In Refrigerator',
        'Voltage': '115V',
        'Amperage': '7.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '81.875" W x 30.75" D x 83.25" H',
        'Weight': '678 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '2/3 HP (bottom-mounted)',
        'Capacity': '72 cu. ft.',
        'Doors': '3',
        'Shelves': '9',
        'Temperature Range': '33°F to 38°F',
        'Price': '$9,254.96',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Triple pane heated glass doors, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Three-door glass merchandiser with massive capacity. Perfect for high-volume display applications.',
        'Use Cases': 'Large retail operations, Commissaries, Institutional dining'
    },

    # TSF Series (3 SKUs with complete data - TSF-35SD-N removed)
    {
        'SKU': 'TSF-23SD-N(-L)',
        'Product Type': 'Reach-in Freezer',
        'Voltage': '115V',
        'Amperage': '5.4A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27" W x 30.375" D x 83.25" H',
        'Weight': '310 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/2 HP, bottom-mounted',
        'Capacity': '19.03 cu. ft.',
        'Doors': '1 (solid)',
        'Shelves': '3',
        'Temperature Range': '-10°F to 0°F',
        'Price': '$4,836.08',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Turbo Freeze function, Smart defrost system, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Single door reach-in freezer with Super Deluxe features. Maintains consistent frozen temperatures with smart defrost.',
        'Use Cases': 'Restaurants, Ice cream shops, Frozen food storage, Bakeries'
    },
    {
        'SKU': 'TSF-49SD-N',
        'Product Type': 'Reach-in Freezer',
        'Voltage': '115V',
        'Amperage': '5.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '54.375" W x 30.375" D x 83.25" H',
        'Weight': '457 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '2/3 HP, bottom-mounted',
        'Capacity': '39.9 cu. ft.',
        'Doors': '2 (solid)',
        'Shelves': '6',
        'Temperature Range': '-10°F to 0°F',
        'Price': '$6,917.22',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Turbo Freeze function, Smart defrost system, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Large capacity two-door freezer with advanced defrost system to maintain optimal performance.',
        'Use Cases': 'Large restaurants, Frozen food distributors, Institutional kitchens'
    },
    {
        'SKU': 'TSF-72SD-N',
        'Product Type': 'Reach-in Freezer',
        'Voltage': '115V',
        'Amperage': '6.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-20P',
        'Dimensions': '81.875" W x 30.375" D x 83.25" H',
        'Weight': '639 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '3/4 HP, bottom-mounted',
        'Capacity': '63.8 cu. ft.',
        'Doors': '3 (solid)',
        'Shelves': '9',
        'Temperature Range': '-10°F to 0°F',
        'Price': '$8,961.76',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, LED interior lighting, Turbo Freeze function, Smart defrost system, Door pressure release device, Field reversible doors, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Three-door commercial freezer with maximum frozen storage capacity. Features smart defrost for energy efficiency.',
        'Use Cases': 'High-volume operations, Central kitchens, Food distributors'
    },

    # M3 Series (11 SKUs with complete data)
    {
        'SKU': 'M3R19-1-N',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.0A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '25.25" W x 31.5" D x 72" H',
        'Weight': '250 lbs',
        'Refrigerant': 'R-600A',
        'Compressor': '1/5 HP',
        'Capacity': '18.44 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$2,873.71',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Compact M3 series refrigerator perfect for tight spaces. Energy-efficient with R-600A refrigerant.',
        'Use Cases': 'Small kitchens, Prep areas, Under-counter applications'
    },
    {
        'SKU': 'M3R24-1-N',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 30.75" D x 78" H',
        'Weight': '270 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '21.6 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$3,389.51',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Versatile single-door refrigerator with M3 series reliability. Popular choice for diverse applications.',
        'Use Cases': 'Restaurants, Cafes, Healthcare facilities, Schools'
    },
    {
        'SKU': 'M3R47-2-N',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '51.75" W x 32.75" D x 83" H',
        'Weight': '401 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '42.3 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$4,545.87',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'Two-door M3 refrigerator offering excellent value and reliability for commercial operations.',
        'Use Cases': 'Commercial kitchens, Restaurants, Institutional foodservice'
    },
    {
        'SKU': 'M3R72-3-N(-AL)(-AR)',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '5.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '77.75" W x 32.75" D x 83" H',
        'Weight': '559 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/2 HP',
        'Capacity': '65.8 cu. ft.',
        'Doors': '3',
        'Shelves': '9',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,204.96',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Three-door refrigerator with maximum storage capacity. M3 series quality at an economical price.',
        'Use Cases': 'Large kitchens, Commissaries, Institutional dining'
    },
    {
        'SKU': 'M3R24-2-N(-L)',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 32.75" D x 83" H',
        'Weight': '270 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '21.6 cu. ft.',
        'Doors': '2 (half doors)',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$3,728.28',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation, Half doors reduce cold air loss',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Half-door configuration minimizes temperature loss while providing easy access to stored items.',
        'Use Cases': 'Busy kitchens, Prep stations, Quick-service restaurants'
    },
    {
        'SKU': 'M3R47-4-N(-AL)(-AR)',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.8A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '51.75" W x 32.75" D x 83" H',
        'Weight': '401 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '42.1 cu. ft.',
        'Doors': '4 (half doors)',
        'Shelves': '6',
        'Temperature Range': '33°F to 38°F',
        'Price': '$5,477.38',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation, Half doors reduce cold air loss',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Four half-door design provides maximum organization and energy efficiency for busy operations.',
        'Use Cases': 'High-traffic kitchens, Multiple station access, Prep areas'
    },
    {
        'SKU': 'M3R72-6-N',
        'Product Type': 'Refrigerator',
        'Voltage': '115V',
        'Amperage': '7.9A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '77.75" W x 32.75" D x 83" H',
        'Weight': '562 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1 HP',
        'Capacity': '65.6 cu. ft.',
        'Doors': '6 (half doors)',
        'Shelves': '9',
        'Temperature Range': '33°F to 38°F',
        'Price': '$6,666.98',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation, Half doors reduce cold air loss',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Six half-door configuration for maximum access points and organization in high-volume operations.',
        'Use Cases': 'Central kitchens, Multiple chef stations, Large institutions'
    },
    {
        'SKU': 'M3F19-1-N',
        'Product Type': 'Freezer',
        'Voltage': '115V',
        'Amperage': '4.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '25.25" W x 33.5" D x 77.125" H',
        'Weight': '194 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '3/8 HP',
        'Capacity': '18.7 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '-10°F to 0°F',
        'Price': '$3,147.11',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Compact M3 series freezer ideal for smaller operations or as supplemental frozen storage.',
        'Use Cases': 'Small restaurants, Bakeries, Ice cream shops'
    },
    {
        'SKU': 'M3F24-1-N',
        'Product Type': 'Freezer',
        'Voltage': '115V',
        'Amperage': '4.4A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 32.75" D x 83" H',
        'Weight': '280 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/2 HP',
        'Capacity': '21.6 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '-10°F to 0°F',
        'Price': '$4,175.36',
        'Features': 'Self-cleaning condenser, Digital temperature control & display, Interior LED lighting, Field reversible doors, Stainless steel interior & exterior, Anti-corrosion coated evaporator, High-density polyurethane insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Single door M3 freezer with reliable performance and energy-efficient operation.',
        'Use Cases': 'Restaurants, Frozen food storage, Ice cream storage'
    },
    {
        'SKU': 'M3H24-1',
        'Product Type': 'Heated Cabinet',
        'Voltage': '115V',
        'Amperage': '8.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '28.75" W x 30.75" D x 78" H',
        'Weight': '250 lbs',
        'Refrigerant': 'N/A',
        'Compressor': 'N/A (950W heating element)',
        'Capacity': '22.7 cu. ft.',
        'Doors': '1',
        'Shelves': '3',
        'Temperature Range': '140°F to 180°F',
        'Price': '$2,880.81',
        'Features': 'Digital temperature control & display, Interior lighting, Magnetic door gaskets, Adjustable shelves, Stainless steel construction, High-density insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Heated holding cabinet maintains safe food temperatures. Ideal for keeping prepared foods at serving temperature.',
        'Use Cases': 'Hot food holding, Catering operations, Buffet service'
    },
    {
        'SKU': 'M3H47-2',
        'Product Type': 'Heated Cabinet',
        'Voltage': '115V',
        'Amperage': '13.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '51.75" W x 30.75" D x 78" H',
        'Weight': '367 lbs',
        'Refrigerant': 'N/A',
        'Compressor': 'N/A (1550W heating element)',
        'Capacity': '42.9 cu. ft.',
        'Doors': '2',
        'Shelves': '6',
        'Temperature Range': '140°F to 180°F',
        'Price': '$3,584.85',
        'Features': 'Digital temperature control & display, Interior lighting, Magnetic door gaskets, Adjustable shelves, Stainless steel construction, High-density insulation',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Two-door heated cabinet with large capacity for high-volume hot holding applications.',
        'Use Cases': 'Large kitchens, Banquet facilities, Institutional foodservice'
    },

    # PST Series (10 SKUs with complete data)
    {
        'SKU': 'PST-28-N(-L)',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.5" W x 34" D x 39.125" H',
        'Weight': '200 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '7.0 cu. ft.',
        'Doors': '1',
        'Shelves': '1',
        'Temperature Range': '33°F to 39°F',
        'Price': '$3,522.85',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Field reversible door',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Compact prep table perfect for sandwich and salad preparation. Cold bunker design maintains temperature with lid open.',
        'Use Cases': 'Sandwich shops, Delis, Small kitchens, Pizza restaurants'
    },
    {
        'SKU': 'PST-48-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '48.25" W x 30" D x 37.625" H',
        'Weight': '220 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/5 HP',
        'Capacity': '12.0 cu. ft.',
        'Doors': '2',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$4,730.75',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Field reversible doors',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Mid-size prep table with two-door storage. Ideal for moderate volume sandwich and salad preparation.',
        'Use Cases': 'Restaurants, Cafes, Delis, Catering kitchens'
    },
    {
        'SKU': 'PST-60-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '8.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '60.25" W x 30" D x 37.625" H',
        'Weight': '280 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '16.0 cu. ft.',
        'Doors': '2',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$5,320.51',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Field reversible doors',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Popular 60-inch prep table with ample workspace and storage. Perfect for busy sandwich operations.',
        'Use Cases': 'Busy delis, Sub shops, Restaurant prep stations'
    },
    {
        'SKU': 'PST-72-N(-AL)(-AR)',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '9.9A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '72.625" W x 30" D x 37.625" H',
        'Weight': '320 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '3/8 HP',
        'Capacity': '19.0 cu. ft.',
        'Doors': '2',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$5,576.73',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Field reversible doors',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Large 72-inch prep table for high-volume operations. Maximum workspace with efficient refrigeration.',
        'Use Cases': 'High-volume sandwich shops, Large delis, Institutional kitchens'
    },
    {
        'SKU': 'PST-28-G-N(-L)',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.5" W x 34" D x 39.125" H',
        'Weight': '200 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '7.0 cu. ft.',
        'Doors': '1 (glass)',
        'Shelves': '1',
        'Temperature Range': '33°F to 39°F',
        'Price': '$3,700.26',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Glass door for product visibility',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Compact prep table with glass door for ingredient visibility. Perfect for front-of-house applications.',
        'Use Cases': 'Display kitchens, Sandwich shops, Cafes'
    },
    {
        'SKU': 'PST-48-G-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '48.25" W x 30" D x 37.625" H',
        'Weight': '220 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/5 HP',
        'Capacity': '12.0 cu. ft.',
        'Doors': '2 (glass)',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$5,676.45',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Glass doors for product visibility',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Glass door prep table combines functionality with merchandising. Shows fresh ingredients to customers.',
        'Use Cases': 'Open kitchens, Fast-casual restaurants, Delis'
    },
    {
        'SKU': 'PST-60-G-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '8.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '60.25" W x 30" D x 37.625" H',
        'Weight': '280 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '16.0 cu. ft.',
        'Doors': '2 (glass)',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$6,305.05',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Glass doors for product visibility',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': '60-inch glass door prep table for operations that value ingredient transparency and freshness display.',
        'Use Cases': 'Premium delis, Upscale sandwich shops, Hotels'
    },
    {
        'SKU': 'PST-72-G-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '9.9A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '72.625" W x 30" D x 37.625" H',
        'Weight': '320 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '3/8 HP',
        'Capacity': '19.0 cu. ft.',
        'Doors': '2 (glass)',
        'Shelves': '2',
        'Temperature Range': '33°F to 39°F',
        'Price': '$6,607.96',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Glass doors for product visibility',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Large glass door prep table combining maximum workspace with ingredient merchandising capabilities.',
        'Use Cases': 'High-end delis, Exhibition kitchens, Large cafeterias'
    },
    {
        'SKU': 'PST-28-D2-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.25" W x 30" D x 37" H',
        'Weight': '200 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '7.0 cu. ft.',
        'Doors': '0 (2 drawers)',
        'Shelves': '1',
        'Temperature Range': '33°F to 39°F',
        'Price': '$4,378.91',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Two drawer design',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Drawer-style prep table provides easy access to ingredients and supplies. Space-saving design.',
        'Use Cases': 'Tight kitchen spaces, Quick-service restaurants, Pizza shops'
    },
    {
        'SKU': 'PST-48-D2R(L)-N',
        'Product Type': 'Sandwich/Salad Prep Table',
        'Voltage': '115V',
        'Amperage': '6.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '48.25" W x 30" D x 37.625" H',
        'Weight': '266 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/5 HP',
        'Capacity': '12.0 cu. ft.',
        'Doors': '1 (+ 2 drawers)',
        'Shelves': '1',
        'Temperature Range': '33°F to 39°F',
        'Price': '$6,006.63',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Cold bunker system, Cutting board included, Refrigerated pan rail, Anti-corrosion coated evaporator, Combination door and drawer design',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'Combination door and drawer prep table offers versatile storage options for different ingredients.',
        'Use Cases': 'Diverse menu operations, Sandwich and pizza shops, Cafes'
    }
]

# Additional products from other series with found pricing
additional_products = [
    # TPR Series (Pizza Prep)
    {
        'SKU': 'TPR-44SD-N',
        'Product Type': 'Pizza Prep Refrigerator',
        'Voltage': '115V',
        'Amperage': '3.2A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '44" W x 32.25" D x 37.125" H',
        'Weight': '320 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/4 HP',
        'Capacity': '14 cu. ft.',
        'Doors': '1',
        'Shelves': '2',
        'Temperature Range': '33°F to 41°F',
        'Price': '$3,970.68',
        'Features': 'Self-cleaning condenser, Digital temperature control, Forced air cold bunker system, 19.25" deep cutting board, Stainless steel construction, Refrigerated pan rail for 6 pans, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Compact pizza prep table with extra-deep cutting board. Forced air system maintains temperature with lid open.',
        'Use Cases': 'Pizza restaurants, Italian restaurants, Small pizzerias'
    },
    {
        'SKU': 'TPR-67SD-N',
        'Product Type': 'Pizza Prep Refrigerator',
        'Voltage': '115V',
        'Amperage': '4.2A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '67" W x 36.25" D x 41" H',
        'Weight': '411 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '2/3 HP',
        'Capacity': '20 cu. ft.',
        'Doors': '2',
        'Shelves': '4',
        'Temperature Range': '33°F to 41°F',
        'Price': '$5,506.14',
        'Features': 'Self-cleaning condenser, Digital temperature control, Forced air cold bunker system, 19.25" deep cutting board, Stainless steel construction, Refrigerated pan rail for 9 pans, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Mid-size pizza prep table with generous topping rail capacity. Ideal for moderate to busy pizzerias.',
        'Use Cases': 'Busy pizzerias, Italian restaurants, Multi-unit operations'
    },
    {
        'SKU': 'TPR-93SD-N',
        'Product Type': 'Pizza Prep Refrigerator',
        'Voltage': '115V',
        'Amperage': '5.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '93" W x 32.25" D x 37.125" H',
        'Weight': '550 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '2/3 HP',
        'Capacity': '31 cu. ft.',
        'Doors': '3',
        'Shelves': '6',
        'Temperature Range': '33°F to 41°F',
        'Price': '$7,324.34',
        'Features': 'Self-cleaning condenser, Digital temperature control, Forced air cold bunker system, 19.25" deep cutting board, Stainless steel construction, Refrigerated pan rail for 12 pans, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Extra-large pizza prep table for high-volume operations. Maximum topping capacity and storage.',
        'Use Cases': 'High-volume pizzerias, Large restaurants, Stadium kitchens'
    },

    # MUR Series (Undercounter)
    {
        'SKU': 'MUR-28-N',
        'Product Type': 'Undercounter Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.2A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.5" W x 31" D x 35.625" H',
        'Weight': '163 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '6.8 cu. ft.',
        'Doors': '1',
        'Shelves': '1',
        'Temperature Range': '33°F to 38°F',
        'Price': '$2,162.57',
        'Features': 'Self-cleaning condenser, Digital temperature control, LED interior lighting, Stainless steel construction, Field reversible door, Anti-corrosion coated evaporator, Heavy-duty casters',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Compact undercounter refrigerator from M3 series. Perfect for tight spaces and bar applications.',
        'Use Cases': 'Bars, Small kitchens, Prep stations, Coffee shops'
    },
    {
        'SKU': 'MUR-72-N',
        'Product Type': 'Undercounter Refrigerator',
        'Voltage': '115V',
        'Amperage': '2.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '72.625" W x 31" D x 35.625" H',
        'Weight': '352 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '18.8 cu. ft.',
        'Doors': '3',
        'Shelves': '3',
        'Temperature Range': '33°F to 38°F',
        'Price': '$3,806.71',
        'Features': 'Self-cleaning condenser, Digital temperature control, LED interior lighting, Stainless steel construction, Field reversible doors, Anti-corrosion coated evaporator, Heavy-duty casters',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'Three-door undercounter refrigerator providing maximum storage in limited height spaces.',
        'Use Cases': 'Bar service, Undercounter storage, Prep stations, Cafes'
    },

    # PUR Series
    {
        'SKU': 'PUR-28-D2-N',
        'Product Type': 'Undercounter Refrigerator (2-Drawer)',
        'Voltage': '115V',
        'Amperage': '6.6A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.5" W x 30" D x 30.5" H',
        'Weight': '165 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '6.8 cu. ft.',
        'Doors': '2 Drawers',
        'Shelves': 'N/A',
        'Temperature Range': '33°F to 38°F',
        'Price': '$4,251.18',
        'Features': 'Self-cleaning condenser, Digital temperature control, Stainless steel construction, Drawer design for easy access, Anti-corrosion coated evaporator, Heavy-duty drawer slides',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'PRO series undercounter with drawers for convenient access. Premium construction and features.',
        'Use Cases': 'Prep stations, Chef bases, Bar service, Cold storage'
    },
    {
        'SKU': 'PUR-60-G-N',
        'Product Type': 'Undercounter Refrigerator (Glass Doors)',
        'Voltage': '115V',
        'Amperage': '8.9A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '60.25" W x 30" D x 30.5" H',
        'Weight': '290 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '17.0 cu. ft.',
        'Doors': '2 Glass',
        'Shelves': '2',
        'Temperature Range': '33°F to 38°F',
        'Price': '$5,363.83',
        'Features': 'Self-cleaning condenser, Digital temperature control, Triple pane heated glass doors, LED interior lighting, Stainless steel construction, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'PRO series glass door undercounter for product display. Premium features with excellent visibility.',
        'Use Cases': 'Display applications, Bars, Cafes, Convenience stores'
    },

    # EUR Series
    {
        'SKU': 'EUR-28-N6-V',
        'Product Type': 'Undercounter Refrigerator',
        'Voltage': '115V',
        'Amperage': '1.2A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.5" W x 31" D x 36.625" H',
        'Weight': '150 lbs',
        'Refrigerant': 'R-600a',
        'Compressor': '1/8 HP',
        'Capacity': '6.76 cu. ft.',
        'Doors': '1',
        'Shelves': '1',
        'Temperature Range': '33°F to 38°F',
        'Price': '$1,544.70',
        'Features': 'Digital temperature control, LED interior lighting, Stainless steel construction, Energy-efficient design, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation, ENERGY STAR',
        'Description': 'E-Line energy-efficient undercounter refrigerator. Budget-friendly with essential features.',
        'Use Cases': 'Small operations, Budget-conscious buyers, Light-duty applications'
    },

    # PWR Series
    {
        'SKU': 'PWR-48-N',
        'Product Type': 'Worktop Refrigerator',
        'Voltage': '115V',
        'Amperage': '6.5A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '48.25" W x 33" D x 38.875" H',
        'Weight': '285 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '12.2 cu. ft.',
        'Doors': '2',
        'Shelves': '2',
        'Temperature Range': '33°F to 38°F',
        'Price': '$4,787.52',
        'Features': 'Self-cleaning condenser, Digital temperature control, Heavy-duty stainless steel worktop, LED interior lighting, Field reversible doors, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation, Made in USA',
        'Description': 'PRO series worktop refrigerator provides refrigeration and work surface in one unit.',
        'Use Cases': 'Prep stations, Small kitchens, Equipment stands, Chef bases'
    },

    # TWR Series
    {
        'SKU': 'TWR-28SD-D2-N',
        'Product Type': 'Worktop Refrigerator with Drawers',
        'Voltage': '115V',
        'Amperage': '2.4A',
        'Phase': 'Single Phase',
        'Frequency': '60Hz',
        'Plug Type': 'NEMA 5-15P',
        'Dimensions': '27.25" W x 31" D x 38.5" H',
        'Weight': '200 lbs',
        'Refrigerant': 'R-290',
        'Compressor': '1/6 HP',
        'Capacity': '8 cu. ft.',
        'Doors': '2 Drawers',
        'Shelves': 'N/A',
        'Temperature Range': '33°F to 38°F',
        'Price': '$2,271.25',
        'Features': 'Digital temperature control, Stainless steel construction, ADA compliant height, Heavy-duty drawer slides, Anti-corrosion coated evaporator',
        'Certifications': 'cETLus, ETL-Sanitation',
        'Description': 'ADA-compliant worktop refrigerator with drawers. Perfect height for accessible design.',
        'Use Cases': 'ADA-compliant kitchens, Prep stations, Healthcare facilities'
    }
]

# Combine all products
all_products = products + additional_products

# Create DataFrame
df = pd.DataFrame(all_products)

# Add metric conversions
df['Dimensions (Metric)'] = df['Dimensions'].apply(convert_dimensions_to_metric)
df['Weight (Metric)'] = df['Weight'].apply(convert_weight_to_metric)

# Convert temperature ranges to metric
def convert_temp_to_metric(temp_range):
    if pd.isna(temp_range) or temp_range == 'N/A':
        return 'N/A'
    
    # Extract numbers from the string
    numbers = re.findall(r'(-?\d+)', temp_range)
    
    if len(numbers) >= 2:
        # Convert Fahrenheit to Celsius
        temp1_c = (float(numbers[0]) - 32) * 5/9
        temp2_c = (float(numbers[1]) - 32) * 5/9
        
        return f"{temp1_c:.1f}°C to {temp2_c:.1f}°C"
    return temp_range

df['Temperature Range (Metric)'] = df['Temperature Range'].apply(convert_temp_to_metric)

# Create a version for the viewer with expected column names
viewer_df = df.copy()
viewer_df = viewer_df.rename(columns={'SKU': 'model'})

# Add additional columns expected by the viewer
viewer_df['source_file'] = viewer_df['model'] + '.pdf'
viewer_df['amps'] = viewer_df['Amperage'].str.extract(r'(\d+\.?\d*)').astype(float, errors='ignore')
viewer_df['capacity_cuft'] = viewer_df['Capacity'].str.extract(r'(\d+\.?\d*)').astype(float, errors='ignore')
viewer_df['hp'] = viewer_df['Compressor'].str.extract(r'(\d+/?\d*|\d+\.?\d*)').fillna('')
viewer_df['doors'] = viewer_df['Doors'].str.extract(r'(\d+)').fillna('0')
viewer_df['shelves'] = viewer_df['Shelves'].str.extract(r'(\d+)').fillna('0')
viewer_df['pans'] = '0'  # Default value since not in original data

# Extract dimensions
dimensions_split = viewer_df['Dimensions'].str.extract(r'(\d+\.?\d*)"?\s*W?\s*x\s*(\d+\.?\d*)"?\s*D?\s*x\s*(\d+\.?\d*)"?\s*H?')
viewer_df['length_in'] = dimensions_split[0].astype(float, errors='ignore')
viewer_df['depth_in'] = dimensions_split[1].astype(float, errors='ignore') 
viewer_df['height_in'] = dimensions_split[2].astype(float, errors='ignore')

# Map existing columns to viewer format (avoid duplicates)
viewer_df['plug_type'] = viewer_df['Plug Type']
viewer_df['phase'] = viewer_df['Phase']
viewer_df['frequency'] = viewer_df['Frequency']
viewer_df['temperature_range'] = viewer_df['Temperature Range']
viewer_df['features'] = viewer_df['Features']
viewer_df['certifications'] = viewer_df['Certifications']
viewer_df['description'] = viewer_df['Description']
viewer_df['use_cases'] = viewer_df['Use Cases']
viewer_df['refrigerant'] = viewer_df['Refrigerant']  # This is now the mapped column, not a duplicate

# Select only the columns we want for the viewer database
viewer_columns = [
    'model', 'source_file', 'Product Type', 'Voltage', 'amps', 'capacity_cuft',
    'hp', 'refrigerant', 'doors', 'shelves', 'pans', 'length_in', 'depth_in', 
    'height_in', 'plug_type', 'phase', 'frequency', 'temperature_range',
    'features', 'certifications', 'description', 'use_cases', 'Price',
    'Weight', 'Dimensions', 'Compressor', 'Capacity'
]

# Create final viewer dataframe with only the columns that exist
final_viewer_columns = [col for col in viewer_columns if col in viewer_df.columns]
viewer_df_final = viewer_df[final_viewer_columns].copy()

# Reorder columns to place metric values next to imperial
columns_order = ['SKU', 'Product Type', 'Description', 'Use Cases', 'Voltage', 'Amperage', 'Phase', 'Frequency', 
                 'Plug Type', 'Dimensions', 'Dimensions (Metric)', 'Weight', 'Weight (Metric)', 
                 'Temperature Range', 'Temperature Range (Metric)', 'Refrigerant', 'Compressor', 
                 'Capacity', 'Doors', 'Shelves', 'Features', 'Certifications', 'Price']
df = df[columns_order]

# Save to Excel file with specific name
excel_filename = 'turbo_air_products.xlsx'
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Products', index=False)
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Products']
    for idx, column in enumerate(df.columns):
        # Calculate max width needed for this column
        max_length = len(str(column))  # Length of column name
        
        # Check each value in the column
        for value in df[column]:
            try:
                cell_length = len(str(value))
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        
        # Set column width (with max limit)
        adjusted_width = min(max_length + 2, 50)
        column_letter = worksheet.cell(row=1, column=idx+1).column_letter
        worksheet.column_dimensions[column_letter].width = adjusted_width

# Save to SQLite database with specific name
sqlite_filename = 'turbo_air_db_online.sqlite'
conn = sqlite3.connect(sqlite_filename)

# Save the original table as expected
df.to_sql('turbo_air_products', conn, if_exists='replace', index=False)

# Save the viewer-compatible table with renamed columns
viewer_df_final.to_sql('products', conn, if_exists='replace', index=False)

# Create an index on model for faster lookups
conn.execute('CREATE INDEX IF NOT EXISTS idx_model ON products(model)')

conn.close()

print(f"Excel file '{excel_filename}' has been created with {len(all_products)} products.")
print(f"SQLite database '{sqlite_filename}' has been created with {len(all_products)} products.")
print(f"Created tables: 'turbo_air_products' (original data) and 'products' (viewer-compatible)")

# Verify the file was created and show table structure
if os.path.exists(sqlite_filename):
    print(f"✓ Verified: {sqlite_filename} exists with size {os.path.getsize(sqlite_filename)} bytes")
    
    # Show what's in the database
    conn = sqlite3.connect(sqlite_filename)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")
    
    # Show products table structure
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    print(f"\nColumns in 'products' table:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Show sample data
    cursor.execute("SELECT model, plug_type, phase, frequency, temperature_range FROM products LIMIT 5")
    samples = cursor.fetchall()
    print(f"\nSample data with new fields:")
    for sample in samples:
        print(f"  Model: {sample[0]}, Plug: {sample[1]}, Phase: {sample[2]}, Freq: {sample[3]}, Temp: {sample[4]}")
    
    conn.close()
else:
    print(f"✗ Error: {sqlite_filename} was not created")

print(f"\nSummary by series:")
print(f"- PRO Series: 6 SKUs")
print(f"- TSR Series: 8 SKUs")
print(f"- TSF Series: 3 SKUs (TSF-35SD-N removed)")
print(f"- M3 Series: 11 SKUs")
print(f"- PST Series: 10 SKUs")
print(f"- TPR Series: 3 SKUs")
print(f"- MUR Series: 2 SKUs")
print(f"- PUR Series: 2 SKUs")
print(f"- EUR Series: 1 SKU")
print(f"- PWR Series: 1 SKU")
print(f"- TWR Series: 1 SKU")
print(f"- TOM Series: 0 SKUs (TOM-40MW-N and TOM-50MW-N removed)")
print(f"\nTotal: {len(all_products)} products with complete specifications including:")
print(f"- Electrical specs (plug type, phase, frequency)")
print(f"- Temperature ranges in both °F and °C")
print(f"- Detailed features and certifications")
print(f"- Product descriptions and use cases")