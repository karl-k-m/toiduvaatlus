import json
import re
import bs4 as bs
import requests
from unidecode import unidecode

# - - - - -

# Sort array by price
def sort_array_by_price(array):
    array = sorted(array, key=lambda k: k['price'])
    return array

# Search shops for the keyword
def find_matching_products(keyword):
    results = []
    
    # Selver
    ids_api_endpoint = 'https://www.selver.ee/api/ext/klevu-search/search/store_code/et?enablePartialSearch=true&resultForZero=true&noOfResultsZero=9&noOfResultsAC=5&enableFilters=false&enableMultiSelectFilters=false&fetchMinMaxPrice=false&showOutOfStockProducts=false&autoComplete=false&noOfResults=8&paginationStartsFrom=0&sortOrder=RELEVANCE&term=%s&category=KLEVU_PRODUCT&applyFilters=&lsqt=&fields=id,itemGroupId&' % keyword
    json_get = requests.get(ids_api_endpoint, timeout=5).text
    ids_data = json.loads(json_get)
    ids = []
    
    for i in ids_data['result']['queryResults'][0]['records']:
        ids.append(i['id'])

    ids_entry = ''
    
    for i in ids:
        ids_entry += ('%2C' + '"%s"'%i)
    ids_entry = ids_entry[3:]
    
    data_api_endpoint = 'https://www.selver.ee/api/catalog/vue_storefront_catalog_et/product/_search?_source_exclude=configurable_options%2Cproduct_nutr_*%2Csgn%2C*.sgn%2Cmsrp_display_actual_price_type%2C*.msrp_display_actual_price_type%2Crequired_options&_source_include=documents%2Cactivity%2Cconfigurable_children.attributes%2Cconfigurable_children.id%2Cconfigurable_children.final_price%2Cconfigurable_children.color%2Cconfigurable_children.original_price%2Cconfigurable_children.original_price_incl_tax%2Cconfigurable_children.price%2Cconfigurable_children.price_incl_tax%2Cconfigurable_children.size%2Cconfigurable_children.sku%2Cconfigurable_children.special_price%2Cconfigurable_children.special_price_incl_tax%2Cconfigurable_children.tier_prices%2Cfinal_price%2Cid%2Cimage%2Cname%2Cnew%2Coriginal_price_incl_tax%2Coriginal_price%2Cprice%2Cprice_incl_tax%2Cproduct_links%2Csale%2Cspecial_price%2Cspecial_to_date%2Cspecial_from_date%2Cspecial_price_incl_tax%2Cstatus%2Ctax_class_id%2Ctier_prices%2Ctype_id%2Curl_path%2Curl_key%2C*image%2C*sku%2C*small_image%2Cshort_description%2Cmanufacturer%2Cproduct_*%2Cextension_attributes.deposit_data%2Cstock%2Cproduct_stocktype%2Cproduct_stocksource%2Cprices%2Cvmo_badges&from=0&request={"query"%3A{"bool"%3A{"filter"%3A{"bool"%3A{"must"%3A[{"terms"%3A{"visibility"%3A[2%2C3%2C4]}}%2C{"terms"%3A{"status"%3A[1]}}%2C{"bool"%3A{"should"%3A[{"terms"%3A{"id"%3A[' + ids_entry+ ']}}%2C{"bool"%3A{"must"%3A[{"terms"%3A{"id_options"%3A[' + ids_entry + ']}}%2C{"match"%3A{"type_id"%3A"configurable"}}]}}]}}]}}}}%2C"aggs"%3A{"agg_terms_category_ids"%3A{"terms"%3A{"field"%3A"category_ids"%2C"size"%3A100}}%2C"agg_terms_category_ids_options"%3A{"terms"%3A{"field"%3A"category_ids_options"%2C"size"%3A100}}%2C"agg_terms_price"%3A{"terms"%3A{"field"%3A"price"}}%2C"agg_range_price"%3A{"range"%3A{"field"%3A"price"%2C"ranges"%3A[{"from"%3A0%2C"to"%3A1}%2C{"from"%3A1%2C"to"%3A2}%2C{"from"%3A2%2C"to"%3A3}%2C{"from"%3A3%2C"to"%3A4}%2C{"from"%3A4%2C"to"%3A5}%2C{"from"%3A5%2C"to"%3A6}%2C{"from"%3A6%2C"to"%3A7}%2C{"from"%3A7%2C"to"%3A8}%2C{"from"%3A8%2C"to"%3A9}%2C{"from"%3A9%2C"to"%3A10}%2C{"from"%3A10%2C"to"%3A20}%2C{"from"%3A20%2C"to"%3A30}%2C{"from"%3A30%2C"to"%3A40}%2C{"from"%3A40%2C"to"%3A50}%2C{"from"%3A50%2C"to"%3A100}%2C{"from"%3A100%2C"to"%3A150}%2C{"from"%3A150%2C"to"%3A300}%2C{"from"%3A300%2C"to"%3A500}%2C{"from"%3A500}]}}}}&size=10000&sort='
    json_get = requests.get(data_api_endpoint, timeout=5).text
    data = json.loads(json_get)

    for i in data['hits']['hits']:
        price = i['_source']['price_incl_tax']
        name = i['_source']['name']
        ean = int(i['_source']['product_main_ean'])
        product_compare_unit_factor = float(i['_source']['product_compare_unit_factor'])
        link = 'https://www.selver.ee/%s' % i['_source']['url_key']
        results.append({'store': 'selver', 'ean': ean, 'name': name, 'price': price/product_compare_unit_factor, 'link': link})

    # Rimi
    html = requests.get('https://www.rimi.ee/epood/ee/otsing?query=%s' % keyword, timeout=5).text
    soup = bs.BeautifulSoup(html, 'html.parser')

    for list_item in soup.find_all('li', class_='product-grid__item'):
        price = list_item.find('p', class_='card__price-per').contents[0]
        if "Ei ole saadaval" not in price:
            price = float(re.sub('[^0-9,,]', '', str(price)).replace(',', '.'))
        else:
            continue
        link = 'rimi.ee' + list_item.find('a', class_="card__url js-gtm-eec-product-click")['href']
        name = list_item.find('p', class_= 'card__name').contents[0]
        results.append({'store': 'rimi', 'ean': None, 'name': name, 'price': price, 'link': link})

    # Prisma
    soup = bs.BeautifulSoup(requests.get('https://www.prismamarket.ee/products/search/%s' % keyword, timeout=5).text, features='html.parser')
    for script in soup.find_all('script'):
        if '$(document).ready(function() {' in str(script):
            for line in str(script).split('\n'):
                if 'page.init' in line:
                    json_raw = line.strip().replace('page.init', '')
                    break
    json_raw = (json_raw.removesuffix(', {' + json_raw[json_raw.rindex('{')+1:])).replace('(', '')
    data = json.loads(str(json_raw))
    
    for i in data['categories'][0]['entries']:
        name = i['name']
        price = i['comp_price']
        ean = i['ean']
        producer = unidecode(i['subname'])
        link = 'https://www.prismamarket.ee/entry/' + str(i['ean'])
        results.append({'store': 'prisma', 'ean': ean, 'name': name, 'price': price, 'link': link, 'producer': producer})

    try:
        for i in data['categories'][1]['entries']:
            name = i['name']
            price = i['comp_price']
            ean = i['ean']
            producer = unidecode(i['subname'])
            link = 'https://www.prismamarket.ee/entry/' + str(i['ean'])
            results.append({'store': 'prisma', 'ean': ean, 'name': name, 'price': price, 'link': link, 'producer': producer})
    except:
        pass

    return sort_array_by_price(results)

# Read product info
def get_product_info(link):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    name = ''
    price = ''

    if 'rimi' in link:
        soup = bs.BeautifulSoup(requests.get(link, headers=headers).text, features='html.parser')
        
        for i in soup.find_all('h3', class_='name'):
            name = i.text.strip()
        
        for i in soup.find_all('p', class_='price-per'):
            i = i.text.strip().replace(' ', '').split('\n')
            price = float(i[0].replace('€/l', '').replace(',', '.').replace('€', ''))

    if 'prisma' in link:
        soup = bs.BeautifulSoup(requests.get(link, headers=headers).text, features='html.parser')
        
        for i in soup.find_all('h1', id='product-name'):
            name = i.text.strip()
        
        for i in soup.find_all('div', class_='details text-right'):
            i = i.text.strip().replace(' ', '').split('\n')
            price = float(i[2].replace('€/l', '').replace(',', '.'))

    if 'selver' in link:
        api_request = 'https://www.selver.ee/api/catalog/vue_storefront_catalog_et/product/_search?from=0&request={"query":{"bool":{"filter":{"terms":{"url_path":["%s"]}}}}}&size=50&sort=' %(link.rsplit('/', 1)[-1])
        json_get = requests.get(api_request).text
        json_text = json.loads(json_get)
        name = json_text['hits']['hits'][0]['_source']['name']
        price = json_text['hits']['hits'][0]['_source']['unit_price']

    return{'name': name, 'price': price}

# Sort by EAN
def sort_by_ean(results):
    sorted_results = {}
    for i in results:
        if i['ean'] not in sorted_results.keys():
            sorted_results[i['ean']] = []
        sorted_results[i['ean']].append(i)
    return sorted_results

# Seperately sort Rimi because e-Rimi doesn't display EAN.
def sort_by_product(results):
    pass