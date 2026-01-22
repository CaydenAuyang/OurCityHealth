# =====================================================================
# REDDIT SCRAPER - NYC Subreddit Post and Comment Extractor
# =====================================================================
# This script scrapes Reddit posts and comments from r/nyc subreddit
# It can navigate through multiple pages and extract comment discussions
# =====================================================================

# Import the libraries we need for web scraping and HTML parsing
import requests                        # For making HTTP requests to download web pages
from bs4 import BeautifulSoup         # For parsing HTML content and finding specific elements
import time                            # For adding delays between requests (to be polite to servers)

def get_subreddit_posts(url, headers):
    """
    Extract post URLs and next page link from a single subreddit page
    
    Args:
        url: The subreddit page URL to scrape
        headers: HTTP headers to send with the request (to look like a real browser)
    
    Returns:
        A tuple containing:
        - List of full URLs for each post found on the page
        - URL for the next page (or None if no next page)
    """
    # Step 1: Download the subreddit page HTML
    response = requests.get(url, headers=headers)  # Send HTTP GET request to download the page
    soup = BeautifulSoup(response.text, 'html.parser')  # Parse the HTML into a searchable structure
    
    # Step 2: Find all post containers on the page
    post_divs = soup.find_all("div", class_="thing")  # Find all div elements with class "thing" (Reddit's post containers)
    post_urls = []                             # Initialize empty list to store post URLs
    
    # Step 3: Extract the URL for each post
    for post in post_divs:                     # Loop through each post container we found
        permalink = post.get("data-permalink")  # Get the permalink attribute (Reddit's unique post path)
        if permalink:                          # If this post has a valid permalink
            full_url = "https://old.reddit.com" + permalink  # Build the complete URL by adding Reddit's domain
            post_urls.append(full_url)         # Add this complete URL to our list
    
    # Step 4: Look for the "next" button to get more pages
    next_button = soup.find("span", class_="next-button")  # Find the next page button element
    next_url = None                            # Initialize next URL as None (assume no next page)
    if next_button:                            # If we found a next button
        next_link = next_button.find("a")      # Look for a link (anchor tag) inside the button
        if next_link and next_link.has_attr("href"):  # If the link exists and has an href attribute
            next_url = next_link["href"]       # Get the URL for the next page
    
    # Return both the post URLs we found and the next page URL
    return post_urls, next_url                 # Return tuple: (list of post URLs, next page URL or None)

def deep_scrape_subreddit(start_url, max_pages=3):
    """
    Scrape multiple pages of a subreddit to get more posts
    
    Args:
        start_url: The first page URL to start scraping from
        max_pages: Maximum number of pages to scrape (default: 3)
    
    Returns:
        Combined list of all post URLs found across all pages
    """
    # Set up HTTP headers to make our requests look like they come from a real browser
    headers = {"User-Agent": "Mozilla/5.0"}    # Pretend to be Mozilla Firefox browser
    all_posts = []                             # Initialize list to store all posts from all pages
    url = start_url                            # Start with the first page URL
    pages = 0                                  # Counter to track how many pages we've processed
    
    # Keep scraping pages until we run out of pages or hit our limit
    while url and pages < max_pages:           # Continue while we have a URL and haven't hit page limit
        print(f"Scraping page: {url}")         # Show which page we're currently scraping
        
        # Get posts from this page and the URL for the next page
        posts, next_url = get_subreddit_posts(url, headers)  # Call our function to scrape this page
        all_posts.extend(posts)                # Add all posts from this page to our master list
        url = next_url                         # Update URL to the next page (or None if no next page)
        pages += 1                             # Increment our page counter
        time.sleep(2)                          # Wait 2 seconds before requesting next page (be polite to Reddit)
    
    return all_posts                           # Return all post URLs we collected from all pages

def scrape_post_comments(post_url, headers):
    """
    Extract comment texts from a specific Reddit post
    
    Args:
        post_url: The URL of the Reddit post to scrape comments from
        headers: HTTP headers to send with the request
    
    Returns:
        List of comment text strings found on the post
    """
    # Step 1: Download the individual post page
    response = requests.get(post_url, headers=headers)  # Send HTTP request to get the post page
    soup = BeautifulSoup(response.text, 'html.parser')  # Parse the HTML into searchable structure
    
    # Step 2: Find all comment containers on the page
    # In old Reddit, each comment is contained within a <div class="entry">
    comments = soup.find_all("div", class_="entry")  # Find all div elements with class "entry" (comment containers)
    comment_texts = []                         # Initialize empty list to store comment texts
    
    # Step 3: Extract text from each comment
    for comment in comments:                   # Loop through each comment container
        # Look for the actual comment text within this container
        comment_body = comment.find("div", class_="usertext-body")  # Find div with class "usertext-body" (actual comment text)
        if comment_body:                       # If we found a comment body
            text = comment_body.get_text(strip=True)  # Extract the text content, removing extra whitespace
            if text:                           # If the text is not empty
                comment_texts.append(text)     # Add this comment text to our list
    
    return comment_texts                       # Return all comment texts we found

def main():
    """
    The main function that demonstrates how to scrape Reddit posts and comments
    This function runs the complete scraping process for r/nyc
    """
    # Step 1: Set up the starting parameters
    start_url = "https://old.reddit.com/r/nyc/"  # The URL for the NYC subreddit (using old Reddit interface)
    headers = {"User-Agent": "Mozilla/5.0"}    # HTTP headers to make our request look like a real browser
    print("Starting deep scrape of r/nyc ...")  # Inform user that we're beginning the scraping process
    
    # Step 2: Scrape multiple pages of the subreddit to get post URLs
    posts = deep_scrape_subreddit(start_url, max_pages=3)  # Get posts from up to 3 pages
    print(f"Found {len(posts)} post URLs.")    # Show how many post URLs we discovered
    
    # Step 3: Process each post to get its comments
    for post in posts:                         # Loop through each post URL we found
        print("\nPost URL:", post)             # Print the URL of the post we're about to process
        
        # Get comments from this specific post
        comments = scrape_post_comments(post, headers)  # Call our function to extract comments
        print(f"Found {len(comments)} comments (showing up to 3):")  # Show how many comments we found
        
        # Display the first few comments as examples
        for comment in comments[:3]:           # Loop through first 3 comments (or fewer if less than 3)
            print(" -", comment)               # Print each comment with a dash prefix
        
        print("=" * 50)                        # Print a line of equals signs as a separator
        time.sleep(1)                          # Wait 1 second before processing next post (be polite to Reddit)

# This is the standard Python pattern for running main() when script is executed directly
if __name__ == "__main__":                    # This condition is True when script is run directly (not imported)
    main()                                     # Execute our main function to start the Reddit scraping process

# =====================================================================
# WHAT THIS SCRIPT DOES:
# 
# 1. Connects to the r/nyc subreddit on Reddit (old.reddit.com interface)
# 2. Scrapes multiple pages to find post URLs (up to 3 pages by default)
# 3. For each post found, visits the post page and extracts comment texts
# 4. Displays the post URLs and first few comments from each post
# 5. Uses polite delays between requests to avoid overwhelming Reddit's servers
# 
# HOW IT WORKS:
# - Uses old.reddit.com because it's easier to scrape than new Reddit
# - Finds posts by looking for HTML elements with class "thing"
# - Extracts post URLs from the "data-permalink" attribute
# - Finds comments by looking for HTML elements with class "usertext-body"
# - Follows pagination by looking for "next-button" elements
# 
# TO RUN THIS SCRIPT:
# python3 reddit_scraper.py
# 
# You'll see:
# - Progress messages as it scrapes each page
# - Post URLs as they're discovered
# - Comment texts from each post (first 3 comments shown)
# - Separator lines between posts for easy reading
# =====================================================================
