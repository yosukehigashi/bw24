#!/usr/bin/env python
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This example shows how to create a complete Responsive Search ad.

Includes creation of: budget, campaign, ad group, ad group ad,
keywords, and geo targeting.

More details on Responsive Search ads can be found here:
https://support.google.com/google-ads/answer/7684791
"""

import sys
import uuid
import os

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

os.environ["GOOGLE_ADS_CONFIGURATION_FILE_PATH"] = "~/Desktop/google_ads.yaml"
CUSTOMER_ID = "6460230654"


def generate_campaign(ib_id=1234511267, cost=500, headlines=None, descriptions=None, keywords=None, client=GoogleAdsClient.load_from_storage(version="v16"), customer_id=CUSTOMER_ID):

    if keywords is None:
        keywords = ["Apples", "Oranges"]
    if descriptions is None:
        descriptions = ["Check this out", "Please"]
    if headlines is None:
        headlines = ["Great", "Incredible", "Amazing"]

    # Create a budget, which can be shared by multiple campaigns.
    campaign_budget = create_campaign_budget(client, customer_id, cost, ib_id)

    campaign_resource_name = create_campaign(
        client, customer_id, campaign_budget, ib_id
    )

    ad_group_resource_name = create_ad_group(
        client, customer_id, campaign_resource_name, ib_id
    )

    create_ad_group_ad(
        client, customer_id, ad_group_resource_name, ib_id, headlines, descriptions
    )

    add_keywords(client, customer_id, ad_group_resource_name, keywords)

    add_geo_targeting(client, customer_id, campaign_resource_name)


def create_ad_text_asset(client, text, pinned_field=None):
    """Create an AdTextAsset.

    Args:
        client: an initialized GoogleAdsClient instance.
        text: text for headlines and descriptions.
        pinned_field: to pin a text asset so it always shows in the ad.

    Returns:
        An AdTextAsset.
    """
    ad_text_asset = client.get_type("AdTextAsset")
    ad_text_asset.text = text
    if pinned_field:
        ad_text_asset.pinned_field = pinned_field
    return ad_text_asset


def create_campaign_budget(client, customer_id, cost, ib_id):
    """Creates campaign budget resource.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      cost: cost in yen
      ib_id: instabase id of venue

    Returns:
      Campaign budget resource name.
    """
    # Create a budget, which can be shared by multiple campaigns.
    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_budget_operation = client.get_type("CampaignBudgetOperation")
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Campaign budget for {str(ib_id)}"
    campaign_budget.delivery_method = (
        client.enums.BudgetDeliveryMethodEnum.STANDARD
    )
    campaign_budget.amount_micros = cost * 1000000

    # Add budget.
    campaign_budget_response = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[campaign_budget_operation]
    )

    return campaign_budget_response.results[0].resource_name


def create_campaign(client, customer_id, campaign_budget, ib_id):
    """Creates campaign resource.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      campaign_budget: a budget resource name.
      ib_id: instabase venue id

    Returns:
      Campaign resource name.
    """
    campaign_service = client.get_service("CampaignService")
    campaign_operation = client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = f"Campaign for {str(ib_id)}"
    campaign.advertising_channel_type = (
        client.enums.AdvertisingChannelTypeEnum.SEARCH
    )

    # Recommendation: Set the campaign to PAUSED when creating it to prevent
    # the ads from immediately serving. Set to ENABLED once you've added
    # targeting and the ads are ready to serve.
    campaign.status = client.enums.CampaignStatusEnum.PAUSED

    # Set the bidding strategy and budget.
    # The bidding strategy for Maximize Clicks is TargetSpend.
    # The target_spend_micros is deprecated so don't put any value.
    # See other bidding strategies you can select in the link below.
    # https://developers.google.com/google-ads/api/reference/rpc/latest/Campaign#campaign_bidding_strategy
    campaign.target_spend.target_spend_micros = 0
    campaign.campaign_budget = campaign_budget

    # Set the campaign network options.
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_partner_search_network = False
    # Enable Display Expansion on Search campaigns. For more details see:
    # https://support.google.com/google-ads/answer/7193800
    campaign.network_settings.target_content_network = True

    # # Optional: Set the start date.
    # start_time = datetime.date.today() + datetime.timedelta(days=1)
    # campaign.start_date = datetime.date.strftime(start_time, _DATE_FORMAT)

    # # Optional: Set the end date.
    # end_time = start_time + datetime.timedelta(weeks=4)
    # campaign.end_date = datetime.date.strftime(end_time, _DATE_FORMAT)

    # Add the campaign.
    campaign_response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_operation]
    )
    resource_name = campaign_response.results[0].resource_name
    print(f"Created campaign {resource_name}.")
    return resource_name


def create_ad_group(client, customer_id, campaign_resource_name, ib_id):
    """Creates ad group.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      campaign_resource_name: a campaign resource name.
      ib_id: instabase venue id

    Returns:
      Ad group ID.
    """
    ad_group_service = client.get_service("AdGroupService")

    ad_group_operation = client.get_type("AdGroupOperation")
    ad_group = ad_group_operation.create
    ad_group.name = f"Adgroup for {str(ib_id)}"
    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
    ad_group.campaign = campaign_resource_name
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD

    # If you want to set up a max CPC bid uncomment line below.
    # ad_group.cpc_bid_micros = 10000000

    # Add the ad group.
    ad_group_response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id, operations=[ad_group_operation]
    )
    ad_group_resource_name = ad_group_response.results[0].resource_name
    print(f"Created ad group {ad_group_resource_name}.")
    return ad_group_resource_name


def create_ad_group_ad(
        client, customer_id, ad_group_resource_name, ib_id, headlines, descriptions
):
    """Creates ad group ad.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      ad_group_resource_name: an ad group resource name.
      ib_id: instabase venue id
      headlines: a list of 3 headlines for ad listing
      descriptions: a list of 2 descriptions for ad listing

    Returns:
      Ad group ad resource name.
    """
    ad_group_ad_service = client.get_service("AdGroupAdService")

    ad_group_ad_operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = ad_group_ad_operation.create
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
    ad_group_ad.ad_group = ad_group_resource_name

    # Set responsive search ad info.
    # https://developers.google.com/google-ads/api/reference/rpc/latest/ResponsiveSearchAdInfo

    # The list of possible final URLs after all cross-domain redirects for the ad.
    ad_group_ad.ad.final_urls.append("https://www.instabase.jp/space/" + str(ib_id))

    # Set a pinning to always choose this asset for HEADLINE_1. Pinning is
    # optional; if no pinning is set, then headlines and descriptions will be
    # rotated and the ones that perform best will be used more often.

    # Headline 1
    served_asset_enum = client.enums.ServedAssetFieldTypeEnum.HEADLINE_1
    pinned_headline = create_ad_text_asset(
        client, headlines[0], served_asset_enum
    )

    # Headline 2 and 3
    ad_group_ad.ad.responsive_search_ad.headlines.extend(
        [
            pinned_headline,
            create_ad_text_asset(client, headlines[1]),
            create_ad_text_asset(client, headlines[2]),
        ]
    )

    # Description 1 and 2
    description_1 = create_ad_text_asset(client, descriptions[0])
    description_2 = create_ad_text_asset(client, descriptions[1])

    ad_group_ad.ad.responsive_search_ad.descriptions.extend(
        [description_1, description_2]
    )

    # Send a request to the server to add a responsive search ad.
    ad_group_ad_response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id, operations=[ad_group_ad_operation]
    )

    for result in ad_group_ad_response.results:
        print(
            f"Created responsive search ad with resource name "
            f'"{result.resource_name}".'
        )


def add_keywords(client, customer_id, ad_group_resource_name, broad_matches):
    """Creates keywords.

    Creates 3 keyword match types: EXACT, PHRASE, and BROAD.

    EXACT: ads may show on searches that ARE the same meaning as your keyword.
    PHRASE: ads may show on searches that INCLUDE the meaning of your keyword.
    BROAD: ads may show on searches that RELATE to your keyword.
    For smart bidding, BROAD is the recommended one.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      ad_group_resource_name: an ad group resource name.
      broad_matches: a list of terms to match broadly
    """
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")

    operations = []

    # Create keywords.
    for keyword in broad_matches:
        ad_group_criterion_operation = client.get_type("AdGroupCriterionOperation")
        ad_group_criterion = ad_group_criterion_operation.create
        ad_group_criterion.ad_group = ad_group_resource_name
        ad_group_criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        ad_group_criterion.keyword.text = keyword
        ad_group_criterion.keyword.match_type = (
            client.enums.KeywordMatchTypeEnum.BROAD
        )

        operations.append(ad_group_criterion_operation)

    # Add keywords
    ad_group_criterion_response = (
        ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations,
        )
    )
    for result in ad_group_criterion_response.results:
        print("Created keyword " f"{result.resource_name}.")


def add_geo_targeting(client, customer_id, campaign_resource_name):
    """Creates geo targets.

    Args:
      client: an initialized GoogleAdsClient instance.
      customer_id: a client customer ID.
      campaign_resource_name: an campaign resource name.

    Returns:
      Geo targets.
    """
    # Geo targeting from user.
    GEO_LOCATION_1 = "Tokyo"
    GEO_LOCATION_2 = "Osaka"
    GEO_LOCATION_3 = "Chiba"

    # LOCALE and COUNTRY_CODE are used for geo targeting.
    # LOCALE is using ISO 639-1 format. If an invalid LOCALE is given,
    # 'es' is used by default.
    LOCALE = "ja"

    # A list of country codes can be referenced here:
    # https://developers.google.com/google-ads/api/reference/data/geotargets
    COUNTRY_CODE = "JP"

    geo_target_constant_service = client.get_service("GeoTargetConstantService")

    # Search by location names from
    # GeoTargetConstantService.suggest_geo_target_constants() and directly
    # apply GeoTargetConstant.resource_name.
    gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")
    gtc_request.locale = LOCALE
    gtc_request.country_code = COUNTRY_CODE

    # The location names to get suggested geo target constants.
    gtc_request.location_names.names.extend(
        [GEO_LOCATION_1, GEO_LOCATION_2, GEO_LOCATION_3]
    )

    results = geo_target_constant_service.suggest_geo_target_constants(
        gtc_request
    )

    operations = []
    for suggestion in results.geo_target_constant_suggestions:
        print(
            "geo_target_constant: "
            f"{suggestion.geo_target_constant.resource_name} "
            f"is found in LOCALE ({suggestion.locale}) "
            f"with reach ({suggestion.reach}) "
            f"from search term ({suggestion.search_term})."
        )
        # Create the campaign criterion for location targeting.
        campaign_criterion_operation = client.get_type(
            "CampaignCriterionOperation"
        )
        campaign_criterion = campaign_criterion_operation.create
        campaign_criterion.campaign = campaign_resource_name
        campaign_criterion.location.geo_target_constant = (
            suggestion.geo_target_constant.resource_name
        )
        operations.append(campaign_criterion_operation)

    campaign_criterion_service = client.get_service("CampaignCriterionService")
    campaign_criterion_response = (
        campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id, operations=[*operations]
        )
    )

    for result in campaign_criterion_response.results:
        print(f'Added campaign criterion "{result.resource_name}".')
