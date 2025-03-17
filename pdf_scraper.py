import requests
import PyPDF2
import io
import re
from datetime import datetime

def download_pdf(url):
    """Download PDF from URL and return as bytes"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None

def parse_schedule_line(line):
    """Parse a single line of schedule data"""
    # Match lines with session numbers in the first column followed by platform data
    full_pattern = r'^\s*(\d+)?\s*(Red|White|Blue)\s+(\d+:\d+\s+[AP]M)\s+(\d+:\d+\s+[AP]M)\s+([MF])\s+([\w+&\s-]+(?:kg)?)\s+([A-E])\s+([\d-]+)\s+(\d+)\s*$'
    match = re.match(full_pattern, line.strip())
    if match:
        return {
            'type': 'platform',
            'session': match.group(1),
            'platform': match.group(2),
            'start_time': match.group(4),
            'gender': match.group(5),
            'weight_class': match.group(6),
            'group': match.group(7),
            'total': match.group(8),
            'lifters': match.group(9)
        }
    return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file with date and session information"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        formatted_output = []
        current_date = None
        current_session = 1
        platform_count = 0
        
        # Date mapping for each session range
        date_ranges = {
            "April 3, 2025": (1, 6),    # Sessions 1-7
            "April 4, 2025": (7, 12),   # Sessions 8-13
            "April 5, 2025": (13, 18),  # Sessions 14-19
            "April 6, 2025": (19, 22)   # Sessions 20-23
        }
        
        # Gender mapping
        gender_map = {
            'W': 'Female',
            'M': 'Male'
        }
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Process platform data lines
            for line in lines:
                # Only process lines that start with platform colors
                if re.match(r'^\s*(Red|White|Blue)\s+', line):
                    platform_pattern = r'(Red|White|Blue)\s+(\d+:\d+\s+[AP]M)\s+(\d+:\d+\s+[AP]M)\s+([MF])\s+([\w+&\s-]+(?:kg)?)\s+([A-G])\s+([\d-]+)\s+(\d+)'
                    platform_match = re.match(platform_pattern, line.strip())
                    
                    if platform_match:
                        platform_count += 1
                        if platform_count > 3:  # If we've seen 3 platforms, increment session
                            platform_count = 1
                            current_session += 1
                        
                        # Determine the current date based on session number
                        for date, (start, end) in date_ranges.items():
                            if start <= current_session <= end:
                                current_date = date
                                break
                        
                        # Combine gender, weight, and group into weight class
                        gender = gender_map[platform_match.group(4)]
                        weight = platform_match.group(5)
                        group = platform_match.group(6)
                        weight_class = f"{gender} {weight} {group}"
                        
                        formatted_line = (f"Date: {current_date} | "
                                       f"Session: {current_session} | "
                                       f"Platform: {platform_match.group(1)} | "
                                       f"Start Time: {platform_match.group(4)} | "
                                       f"Weight Class: {weight_class} | "
                                       f"Entry Total: {platform_match.group(7)} | "
                                       f"Lifters: {platform_match.group(8)}")
                        formatted_output.append(formatted_line)
        
        return '\n'.join(formatted_output)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def main():
    url = "https://assets.contentstack.io/v3/assets/blteb7d012fc7ebef7f/blt207e15f0bc24569c/67cba7f73661f24149ccbe4e/2025_-_Masters_-_Preliminary_Schedule.pdf"
    
    pdf_file = download_pdf(url)
    if not pdf_file:
        return
    
    text = extract_text_from_pdf(pdf_file)
    if not text:
        return
    
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    print("Text extracted successfully and saved to 'extracted_text.txt'")

if __name__ == "__main__":
    main() 