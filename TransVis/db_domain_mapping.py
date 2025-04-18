"""
VisEval 数据库 ID 到业务领域的映射。
此映射表根据数据库名称推断其可能属于的业务领域。
可以根据需要调整和扩展此映射表，而不必修改主转换脚本。
"""

DB_DOMAIN_MAPPING = {
    # 教育相关
    "activity_1": "Education",
    "student_1": "Education",
    "student_assessment": "Education",
    "student_transcripts_tracking": "Education",
    "university_basketball": "Education",
    "school_finance": "Education",
    "school_player": "Education",
    "school_bus": "Education",
    "scholar": "Education",
    "icfp_1": "Education",
    "protein_institute": "Education",
    
    # 金融相关
    "small_bank_1": "Finance",
    "insurance_policies": "Finance",
    "insurance_fnol": "Finance",
    "insurance_and_eClaims": "Finance",
    "tracking_share_transactions": "Finance",
    "loan_1": "Finance",
    "solvency_ii": "Finance",
    "products_for_hire": "Finance",
    "real_estate_properties": "Finance",
    
    # 娱乐相关
    "movie_1": "Entertainment",
    "music_1": "Entertainment",
    "music_2": "Entertainment",
    "music_4": "Entertainment",
    "tvshow": "Entertainment",
    "musical": "Entertainment",
    "imdb": "Entertainment",
    "game_1": "Entertainment",
    
    # 交通相关
    "flight_4": "Transportation",
    "flight_company": "Transportation",
    "train_station": "Transportation",
    "railway": "Transportation",
    "ship_1": "Transportation",
    "ship_mission": "Transportation",
    
    # 医疗健康
    "hospital_1": "Healthcare",
    "medicine_enzyme_interaction": "Healthcare",
    
    # 体育运动
    "soccer_1": "Sports",
    "soccer_2": "Sports",
    "sports_competition": "Sports",
    "wrestler": "Sports",
    "swimming": "Sports",
    "formula_1": "Sports",
    "wta_1": "Sports",
    "race_track": "Sports",
    "match_season": "Sports",
    "gymnast": "Sports",
    "game_injury": "Sports",
    
    # 零售商业
    "store_1": "Retail",
    "store_product": "Retail",
    "shop_membership": "Retail",
    "tracking_orders": "Retail",
    "product_catalog": "Retail",
    "products_gen_characteristics": "Retail",
    
    # 技术与通信
    "network_1": "Technology",
    "network_2": "Technology",
    "phone_1": "Technology",
    "phone_market": "Technology",
    "tracking_software_problems": "Technology",
    
    # 餐饮与住宿
    "restaurant_1": "Hospitality",
    "restaurants": "Hospitality",
    "inn_1": "Hospitality",
    
    # 天气与环境
    "station_weather": "Weather & Environment",
    "storm_record": "Weather & Environment",
    
    # 政府与公共服务
    "local_govt_mdm": "Government & Public Services",
    "local_govt_and_lot": "Government & Public Services",
    "local_govt_in_alabama": "Government & Public Services",
    
    # 媒体与传播
    "news_report": "Media & Communication",
    "journal_committee": "Media & Communication",
    
    # 人力资源
    "hr_1": "Human Resources",
    
    # 艺术与文化
    "orchestra": "Arts & Culture",
    "theme_gallery": "Arts & Culture",
    "mountain_photos": "Arts & Culture",
    "museum_visit": "Arts & Culture",
    "performance_attendance": "Arts & Culture",
    
    # 农业与食品
    "farm": "Agriculture & Food",
    
    # 其他/通用
    "yelp": "Consumer Services",
    "gas_company": "Energy & Utilities",
    "manufactory_1": "Manufacturing",
    "manufacturer": "Manufacturing",
    "machine_repair": "Industrial Services",
    "wedding": "Personal Events",
    "party_people": "Personal Events",
    "party_host": "Personal Events",
    "voter_1": "Politics",
    "voter_2": "Politics",
    "perpetrator": "Law & Security",
    "pilot_record": "Aviation",
    "poker_player": "Gaming",
    "roller_coaster": "Amusement",
    "riding_club": "Recreation",
    "tracking_grants_for_research": "Research & Development",
    "workshop_paper": "Academic",
    "world_1": "Geography",
    "geo": "Geography",
    "wine_1": "Food & Beverage",
    "sakila_1": "Business",
    "program_share": "Software",
    "singer": "Music & Entertainment",
    "pets_1": "Animal Care",
    "scientist_1": "Science & Research",
    "salaries": "Employment",
}

# 当找不到对应映射时的默认领域
DEFAULT_DOMAIN = "General Visualization"

def get_domain_for_db_id(db_id):
    """
    根据数据库 ID 获取对应的业务领域。
    如果找不到对应的映射，返回默认领域。
    
    Args:
        db_id (str): VisEval 数据库的 ID。
        
    Returns:
        str: 与该数据库对应的业务领域。
    """
    return DB_DOMAIN_MAPPING.get(db_id, DEFAULT_DOMAIN) 