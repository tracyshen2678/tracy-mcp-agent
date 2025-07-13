from adapters.ytj_adapter import YTJAdapter
import pprint

ytj = YTJAdapter()

print("🔍 Fetching company details...")
result = ytj.fetch_company_details("1805485-9")
print("✅ Result from V3:")
print(result)

print("\n🔍 Searching companies with keyword 'KPMG'...")
search_result = ytj.search_companies("KPMG")
print("✅ Search result:")
print(search_result)


print("🔍 Testing industry peer and partner lookup for 1805485-9")
result = ytj.find_industry_peers_and_partners("1805485-9")
pprint.pprint(result)



