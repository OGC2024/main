from util import *


def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):

    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat/r.speed + r.service_time)

    # A solution is a list of bundles
    solution = []

    #------------- Custom algorithm code starts from here --------------#

    car_rider = None
    for r in all_riders:
        if r.type == 'CAR':
            car_rider = r

    all_bundles = []
    all_orders_tmp = all_orders.copy()
    # Create initial bundles using a greedy approach based on distance
    while all_orders_tmp:
        ord = all_orders_tmp.pop(0)
        new_bundle = Bundle(all_orders, car_rider, [ord.id], [ord.id], ord.volume, dist_mat[ord.id, ord.id + K])
        
        # Try to add the nearest orders to the current bundle
        while True:
            nearest_order = None
            min_dist = float('inf')
            for other_ord in all_orders_tmp:
                dist = dist_mat[ord.id, other_ord.id]
                if dist < min_dist and new_bundle.total_volume + other_ord.volume <= car_rider.capa:
                    min_dist = dist
                    nearest_order = other_ord

            if nearest_order:
                new_bundle.shop_seq.append(nearest_order.id)
                new_bundle.dlv_seq.append(nearest_order.id)
                new_bundle.total_volume += nearest_order.volume
                new_bundle.total_dist += min_dist

                feasibility_check = test_route_feasibility(all_orders, car_rider, new_bundle.shop_seq, new_bundle.dlv_seq)
                if feasibility_check == 0:  # Feasible
                    all_orders_tmp.remove(nearest_order)
                    new_bundle.update_cost()
                else:
                    # Remove last added order if not feasible
                    new_bundle.shop_seq.pop()
                    new_bundle.dlv_seq.pop()
                    new_bundle.total_volume -= nearest_order.volume
                    new_bundle.total_dist -= min_dist
                    break
            else:
                break
        
        all_bundles.append(new_bundle)
        car_rider.available_number -= 1
    best_obj = sum((bundle.cost for bundle in all_bundles)) / K
    print(f'Best obj = {best_obj}')
    print(all_bundles)

    # Very stupid random merge algorithm
    while True:

        iter = 0
        max_merge_iter = 1000
        
        while iter < max_merge_iter:
            bundle1, bundle2 = select_two_bundles(all_bundles)
            new_bundle = try_merging_bundles(K, dist_mat, all_orders, bundle1, bundle2)
            if new_bundle is not None:
                all_bundles.remove(bundle1)
                bundle1.rider.available_number += 1
                
                all_bundles.remove(bundle2)
                bundle2.rider.available_number += 1

                all_bundles.append(new_bundle)
                new_bundle.rider.available_number -= 1

                cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
                if cur_obj < best_obj:
                    best_obj = cur_obj
                    print(f'Best obj = {best_obj}')

            else:
                iter += 1

            if time.time() - start_time > timelimit:
                break

        if time.time() - start_time > timelimit:
            break


        for bundle in all_bundles:
            new_rider = get_cheaper_available_riders(all_riders, bundle.rider)
            if new_rider is not None:
                old_rider = bundle.rider
                if try_bundle_rider_changing(all_orders, dist_mat, bundle, new_rider):
                    old_rider.available_number += 1
                    new_rider.available_number -= 1

                if time.time() - start_time > timelimit:
                    break


        cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
        if cur_obj < best_obj:
            best_obj = cur_obj
            print(f'Best obj = {best_obj}')
    print(iter)

    # Solution is a list of bundle information
    solution = [
        # rider type, shop_seq, dlv_seq
        [bundle.rider.type, bundle.shop_seq, bundle.dlv_seq]
        for bundle in all_bundles
    ]

    #------------- End of custom algorithm code--------------#



    return solution
    