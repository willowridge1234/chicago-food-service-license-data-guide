# Publication metadata and checks

This file records the intended GitHub settings so publication is reproducible.

- Repository: `willowridge1234/chicago-food-service-license-data-guide`
- Visibility: public
- Default branch: `main`
- Description: `A practical guide and CSV tool for finding, correctly interpreting, deduplicating, and lawfully using newly issued Chicago food-service license records to spot new restaurant openings.`
- Topics: `b2b-sales`, `lead-generation`, `chicago`, `restaurant-leads`, `open-data`,
  `public-records`, `data-cleaning`, `restaurant-openings`
- Website: leave blank; the README contains the disclosed tagged commercial link

After publication, verify without authentication:

1. `https://github.com/willowridge1234/chicago-food-service-license-data-guide` returns
   HTTP 200.
2. The anonymous GitHub API shows `private: false`, the exact description, and all
   topics:
   `https://api.github.com/repos/willowridge1234/chicago-food-service-license-data-guide`
3. `README.md`, `MEASUREMENT.md`, `LICENSE`, both example CSVs, the cleaned example
   output, the tool, and the tests render at their raw URLs.
4. Every first-party and official external link resolves; the tagged actor link
   preserves its query parameters and lands on
   `apify.com/rook-data-tools/new-food-service-license-leads`.
5. A clean anonymous clone contains the same commit as the publish-ready artifact.
6. Run `python3 -m unittest discover -s tests -v` in that clone — expect 11 passing
   tests.
