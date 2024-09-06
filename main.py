"""This script serves as an example on how to use Python 
   & Playwright to scrape/extract data from Google Maps"""

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys


@dataclass
class House:
    """holds house data"""

    address: str = None
    price: str = None
    bedrooms: str = None
    baths: str = None
    build_area: str = None
    special_notes: str = None

@dataclass
class HouseList:
    """holds list of House objects,
    and save to both excel and csv
    """
    house_list: list[House] = field(default_factory=list)
    save_at = 'output'

    def dataframe(self):
        """transform house_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(house) for house in self.house_list), sep="_"
        )

    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file

        Args:
            filename (str): filename
        """

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file

        Args:
            filename (str): filename
        """

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)

def main():
    ########
    # input 
    ########

    # read search from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    parser.add_argument("-f", "--forType", type=str)
    #TODO:Manali Serach for filters
    args = parser.parse_args()

    if args.total:
        total = args.total
    else:
        # if no total is passed, we set the value to random big number
        total = 1_000_000

    if args.search:
        search_text = args.search
    else:
        print('Error occured: You must either pass the -s search argument')
        sys.exit()

    if args.forType:
        for_type = args.forType
    else:
        for_type="sale"

    # ###########
    # # scraping
    # ###########
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.redfin.com/", timeout=30000)
        # wait is added for dev phase. can remove it in production
        page.wait_for_timeout(5000)


        if search_text:
            print(f"-----\nLooking for homes at {search_text}".strip() + f" for {for_type}")

            page.locator('//input[@id="search-box-input" and @title="City, Address, School, Agent, ZIP"]').fill(search_text)
            page.wait_for_timeout(3000)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # Check if Did you mean dialog opened. If so select 1st opetion
            if page.locator('//div[@class="guts"]').count() >= 0:
                page.locator('//div[@class="item-row item-row-show-sections clickable"]').first.click()
                page.wait_for_timeout(5000)

            # Check for rent
            if for_type == 'rent':
                page.get_by_role("button", name="For sale").click()
                # page.locator('//div[@class="RichSelect__label flex align-center"]').click() #("For Sale").click()
                page.wait_for_timeout(5000)

                page.locator('//input[@name="forRent"]').check()
                page.wait_for_timeout(3000)

                page.get_by_role("button", name="Done").click()
                page.wait_for_timeout(3000)
            # Find out total count of listing to be stored
            listing_count = page.locator('//div[@id="MapHomeCard_0"]//div//div//a[contains(@class, "link-and-anchor")]').count()
            if listing_count >= total:
                listing_count = total
                print(f"Storing {listing_count} house listing..")
            else:
                print(f"Storing {listing_count} house listing..")

            houses_list = HouseList()
            # scraping
            count = 0
            while count < listing_count:
                print(f"{count+1} House listing:")
                try:
                    page.wait_for_timeout(5000)
                    address_xpath = '//div[@class="bp-Homecard__Address flex align-center color-text-primary font-body-xsmall-compact"]'
                    price_xpath = '//span[@class="bp-Homecard__Price--value"]'
                    bedrooms_xpath = '//span[@class="bp-Homecard__Stats--beds text-nowrap"]'
                    baths_xpath = '//span[@class="bp-Homecard__Stats--baths text-nowrap"]'
                    build_area_xpath = '//span[@class="bp-Homecard__LockedStat--value"]'
                    specials_xpath = '//div[@class="KeyFactsExtension"]'

                    house = House()

                    if page.locator(address_xpath).count() > 0:
                        house.address = page.locator(address_xpath).all()[count].inner_text()
                    else:
                        house.address = ""
                    print(f"House address: {house.address}")

                    if page.locator(price_xpath).count() > 0:
                        house.price = page.locator(price_xpath).all()[count].inner_text()
                    else:
                        house.price = ""
                    print(f"House price: {house.price}")

                    if page.locator(bedrooms_xpath).count() > 0:
                        house.bedrooms = page.locator(bedrooms_xpath).all()[count].inner_text()
                    else:
                        house.bedrooms = ""
                    print(f"House bedrooms: {house.bedrooms}")

                    if page.locator(baths_xpath).count() > 0:
                        house.baths = page.locator(baths_xpath).all()[count].inner_text()
                    else:
                        house.baths = ""
                    print(f"House baths: {house.baths}")

                    if page.locator(build_area_xpath).count() > 0:
                        house.build_area = page.locator(build_area_xpath).all()[count].inner_text() + "sq ft"
                    else:
                        house.build_area = ""
                    print(f"House build area: {house.build_area}")

                    if page.locator(specials_xpath):
                        special_note= page.locator(specials_xpath).all()[count].inner_text()
                        house.special_notes = special_note.replace(" • ", "; ")
                    else:
                        house.special_notes = ""
                    print(f"House specials: {house.special_notes}")

                    houses_list.house_list.append(house)
                except Exception as e:
                    print(f'Error occured: {e}')

                count = count + 1

            #########
            # output
            #########
            houses_list.save_to_excel(f"HouseListingData_{for_type}_{search_text}".replace(' ', '_'))
            houses_list.save_to_csv(f"HouseListingData_{for_type}_{search_text}".replace(' ', '_'))

        browser.close()


if __name__ == "__main__":
    main()