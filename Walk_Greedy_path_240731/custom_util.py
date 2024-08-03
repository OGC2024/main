from util import *

from itertools import permutations

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