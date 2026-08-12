# Cambodia RSS findings

## Official source verified

National Bank of Cambodia social media page lists these RSS feeds:

- News: http://www.nbc.org.kh/rss/rss_feed.php?feed=news
- Speeches: http://www.nbc.org.kh/rss/rss_feed.php?feed=speech
- Press releases: http://www.nbc.org.kh/rss/rss_feed.php?feed=press

Source page: https://www.nbc.gov.kh/english/about_the_bank/social_network.php

## Local media candidates

Khmer Times official site exposes Business and Press Releases categories. Search results and the site's WordPress structure indicate these feed endpoints:

- Business: https://www.khmertimeskh.com/category/business/feed/
- Technology tag: https://www.khmertimeskh.com/tag/technology/feed/
- Press Releases: https://www.khmertimeskh.com/category/press-releases/feed/

Source site: https://www.khmertimeskh.com/

## Notes

The NBC feeds are official and directly documented by NBC. Khmer Times category/tag feeds are WordPress-style endpoints and should be checked programmatically before production use. RSS candidates from search results that were not sufficiently verified should not be added automatically.
