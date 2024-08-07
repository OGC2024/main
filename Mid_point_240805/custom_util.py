from util import *

from itertools import permutations

import math

def custom_try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle2, all_riders):
    merged_orders = bundle1.shop_seq + bundle2.shop_seq
    total_volume = get_total_volume(all_orders, merged_orders)
    best_bundle = None
    min_total_cost = float('inf')
    for rider in all_riders:
        if rider.available_number > 0 :
            if total_volume <= rider.capa and len(merged_orders) <= 5:
                for shop_pem in permutations(merged_orders):
                    for dlv_pem in permutations(merged_orders):
                        feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                        if feasibility_check == 0:  # feasible!
                            total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                            temp_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), bundle1.total_volume + bundle2.total_volume, total_dist)
                            temp_bundle.update_cost()

                            if temp_bundle.cost < min_total_cost:
                                min_total_cost = temp_bundle.cost
                                best_bundle = temp_bundle

    return best_bundle

def custom_try_bundle_rider_changing(all_orders, dist_mat, bundle, all_riders):
    old_rider = bundle.rider
    best_shop_seq = None
    best_dlv_seq = None
    best_rider = None
    min_total_cost = float('inf')
    
    for rider in all_riders:
        if bundle.total_volume <= rider.capa:
            orders = bundle.shop_seq
            
            for shop_pem in permutations(orders):
                for dlv_pem in permutations(orders):
                    feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                    if feasibility_check == 0:  # feasible!
                        total_dist = get_total_distance(len(all_orders), dist_mat, shop_pem, dlv_pem)
                        bundle.shop_seq = list(shop_pem)
                        bundle.dlv_seq = list(dlv_pem)
                        bundle.rider = rider
                        bundle.total_dist = total_dist
                        bundle.update_cost()
                        if bundle.cost < min_total_cost:
                            min_total_cost = bundle.cost
                            best_shop_seq = list(shop_pem)
                            best_dlv_seq = list(dlv_pem)
                            best_rider = rider

    if best_shop_seq and best_dlv_seq and best_rider:
        # Note: in-place replacing!
        bundle.shop_seq = best_shop_seq
        bundle.dlv_seq = best_dlv_seq
        bundle.rider = best_rider
        bundle.total_dist = get_total_distance(len(all_orders), dist_mat, best_shop_seq, best_dlv_seq)
        bundle.update_cost()  # update the cost with the best sequences and rider
        if old_rider != best_rider :
            old_rider.available_number += 1
            best_rider.available_number -= 1
        return True

    return False

def count_bundles(all_bundles):
    counts = {
    'WALK': {'total': 0, 'lengths': {}},
    'BIKE': {'total': 0, 'lengths': {}},
    'CAR': {'total': 0, 'lengths': {}}
    }

    # 각 요소를 순회하며 카운팅
    for bundle in all_bundles:
        transport_type = bundle.rider.type
        counts[transport_type]['total'] += 1
    
        length = len(bundle.shop_seq)  # `shop_seq`의 길이를 기준으로 한다.
        if length not in counts[transport_type]['lengths']:
            counts[transport_type]['lengths'][length] = 0
        counts[transport_type]['lengths'][length] += 1

    # 결과 출력
    for transport_type, data in counts.items():
        total_count = data['total']
        print(f"{transport_type}: 총 {total_count}개")
        for length, count in sorted(data['lengths'].items()):
            print(f"  길이 {length}: {count}개")
    
def avg_loc(all_orders, all_bundles):
    bundles_index = [bundle.shop_seq for bundle in all_bundles]
    bundles_avg_loc = []
    for index_seq in bundles_index:
        ords_loc = [((order.shop_lat, order.shop_lon), (order.dlv_lat, order.dlv_lon)) for order in all_orders if order.id in index_seq]
        bundle_loc = np.zeros((2,2))
        for shop_loc, dlv_loc in ords_loc:
            bundle_loc[0] += np.array(shop_loc)
            bundle_loc[1] += np.array(dlv_loc)
        bundle_loc /= len(ords_loc)     
        bundles_avg_loc.append(bundle_loc)

    return bundles_avg_loc

def haversine_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # 지구의 반지름 (킬로미터)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance
    
def dist_mat_by_loc(all_bundles_avg_loc):
    
    N = len(all_bundles_avg_loc)
    bundles_dist_mat = np.zeros((2 * N, 2 * N))

    for i in range(N):
        for j in range(N):
            # 픽업 지점 간 거리
            bundles_dist_mat[i][j] = haversine_distance(all_bundles_avg_loc[i][0], all_bundles_avg_loc[j][0])
        
            # 배송 지점과 픽업 지점 간 거리
            bundles_dist_mat[i + N][j] = haversine_distance(all_bundles_avg_loc[i][1], all_bundles_avg_loc[j][0])
        
            # 픽업 지점과 배송 지점 간 거리
            bundles_dist_mat[i][j + N] = haversine_distance(all_bundles_avg_loc[i][0], all_bundles_avg_loc[j][1])
        
            # 배송 지점 간 거리
            bundles_dist_mat[i + N][j + N] = haversine_distance(all_bundles_avg_loc[i][1], all_bundles_avg_loc[j][1])
    
    return bundles_dist_mat