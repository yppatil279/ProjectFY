import requests
from bs4 import BeautifulSoup
import urllib.parse

def scrape_coursera(course_name):
    """
    Scrapes Coursera to get top-rated courses for the given course name.
    """
    search_url = f"https://www.coursera.org/search?query={urllib.parse.quote(course_name)}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            courses = []
            # This selector looks for anchor tags that wrap course cards
            course_tags = soup.select('a[href^="/learn/"]')

            seen = set()
            for tag in course_tags:
                title = tag.get_text(strip=True)
                href = tag.get('href')

                if href and href not in seen and title:
                    full_link = "https://www.coursera.org" + href
                    courses.append((title, full_link))
                    seen.add(href)

                if len(courses) >= 5:
                    break

            return courses
        else:
            print(f"Failed to access Coursera. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error during scraping Coursera: {e}")
        return []

def get_course_recommendations(course_name):
    if course_name.lower() == 'python':
        return [
            ("Python Official Docs", "https://docs.python.org/3/tutorial/"),
            ("W3Schools Python", "https://www.w3schools.com/python/"),
            ("Real Python Tutorials", "https://realpython.com/"),
            ("FreeCodeCamp Python", "https://www.freecodecamp.org/learn/scientific-computing-with-python/"),
            ("Python.org Getting Started", "https://www.python.org/about/gettingstarted/")
        ]

    return scrape_coursera(course_name)

def main():
    course_input = input("Enter the course you want to learn: ").strip()
    recommendations = get_course_recommendations(course_input)

    if recommendations:
        print("\nTop course recommendations from Coursera:")
        for idx, (title, link) in enumerate(recommendations, 1):
            print(f"{idx}. {title}\n   {link}")
    else:
        print("No course recommendations found.")

if __name__ == "__main__":
    main()
