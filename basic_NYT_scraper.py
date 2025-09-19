# =====================================================================
# NYT SCRAPER - Simple New York Times Article URL Extractor
# =====================================================================
# This is a basic script that finds and prints all article URLs
# from the New York Times homepage using the newspaper library
# =====================================================================

# Import the newspaper library - this helps us automatically find articles on news websites
import newspaper                           # Library that can automatically discover articles on news sites

def main():
    """
    The main function that does all the work of finding NYT article URLs
    This function will run when we execute this script
    """
    # Step 1: Create a newspaper "source" object for the New York Times website
    # This tells the newspaper library to analyze nytimes.com and find all articles
    nytimes_paper = newspaper.build('https://www.nytimes.com', memoize_articles=False)
    # newspaper.build() - Creates a source object that finds articles on a website
    # 'https://www.nytimes.com' - The website we want to analyze
    # memoize_articles=False - Don't cache articles (always get fresh ones)
    
    # Step 2: Loop through each article that the newspaper library found
    # and print its URL to the screen
    for article in nytimes_paper.articles:    # Loop through each article object found
        print(article.url)                    # Print the URL of this article to the console
        # article.url - Gets the web address (URL) of each article

# This is a standard Python pattern that runs main() only when script is executed directly
if __name__ == "__main__":                    # This condition checks if script is run directly (not imported)
    main()                                     # Execute our main function to start the article discovery process

# =====================================================================
# WHAT THIS SCRIPT DOES:
# 
# 1. Connects to the New York Times website (nytimes.com)
# 2. Automatically discovers all article links on the homepage
# 3. Prints each article URL to the screen
# 4. That's it! Simple and straightforward.
# 
# TO RUN THIS SCRIPT:
# python3 NYT_scraper.py
# 
# You'll see a list of URLs printed to your terminal, one per line.
# Each URL is a link to a New York Times article.
# =====================================================================
