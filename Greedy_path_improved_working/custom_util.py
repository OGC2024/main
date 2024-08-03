from util import *
import math
from itertools import permutations, combinations

# 2024-08-03 : all_partitions, find_nearest_bundles, custom_try_merging_multiple_bundles_by_distance, simulated_annealing 함수 추가

def find_nearest_bundles(dist_mat, all_bundles):
    nearest_pairs = []
    for i, bundle1 in enumerate(all_bundles):
        min_dist = float('inf')
        nearest_bundle = None
        for j, bundle2 in enumerate(all_bundles):
            if i != j:
                dist = dist_mat[bundle1.shop_seq[-1], bundle2.shop_seq[0]] #단순하게 bundle1의 pickup 지점의 끝과, bundle2의 pickup 지점의 시작 사이의 거리를
                if dist < min_dist:
                    min_dist = dist
                    nearest_bundle = bundle2
        if nearest_bundle:
            nearest_pairs.append((min_dist, bundle1, nearest_bundle))
    nearest_pairs = sorted(nearest_pairs, key=lambda x: x[0])
    print(f'Nearest pairs: {nearest_pairs}')  # 디버깅 출력
    return nearest_pairs

def all_partitions(orders):
    if len(orders) == 1:
        yield [orders]
        return

    first = orders[0]
    for smaller in all_partitions(orders[1:]):
        # insert `first` in each of the subpartition's subsets
        for n, subset in enumerate(smaller):
            yield smaller[:n] + [[first] + subset] + smaller[n + 1:]
        # put `first` in its own subset
        yield [[first]] + smaller

def filter_partitions(orders, num_parts):
    partitions = list(all_partitions(orders))
    return [p for p in partitions if len(p) == num_parts]

def evaluate_bundles(bundles):
    total_cost = sum(bundle.cost for bundle in bundles)
    return total_cost

def custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, bundles, all_riders):
    merged_orders = list(set([order for bundle in bundles for order in bundle.shop_seq]))  # 중복 주문 제거
    total_volume = get_total_volume(all_orders, merged_orders)
    best_bundles = []
    min_total_cost = float('inf')

    #print(f'merged_orders : {merged_orders}')

    # Try to merge all orders into one bundle
    if len(merged_orders) <= 5:
        for rider in all_riders:
            if rider.available_number > 0 and total_volume <= rider.capa:
                for shop_pem in permutations(merged_orders):
                    for dlv_pem in permutations(merged_orders):
                        feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                        if feasibility_check == 0:
                            total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                            temp_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), total_volume, total_dist)
                            temp_bundle.update_cost()
                            current_cost = evaluate_bundles([temp_bundle])
                            if current_cost < min_total_cost:
                                min_total_cost = current_cost
                                best_bundles = [temp_bundle]
                                #print(f'one bundle : {best_bundles}')

    # Try to split into two bundles
    if len(merged_orders) > 1:
        two_partitions = filter_partitions(merged_orders, 2)
        for partition in two_partitions:
            candidate_bundles = []
            valid_partition = True
            for part in partition:
                part_volume = get_total_volume(all_orders, part)
                part_bundle = None
                for rider in all_riders:
                    if rider.available_number > 0 and part_volume <= rider.capa:
                        for shop_pem in permutations(part):
                            for dlv_pem in permutations(part):
                                feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                                if feasibility_check == 0:
                                    total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                                    part_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), part_volume, total_dist)
                                    part_bundle.update_cost()
                                    candidate_bundles.append(part_bundle)
                                    break
                            if part_bundle:
                                break
                    if part_bundle:
                        break
                if not part_bundle:
                    valid_partition = False
                    break

            if valid_partition and len(candidate_bundles) == 2:
                current_cost = evaluate_bundles(candidate_bundles)
                if current_cost < min_total_cost:
                    min_total_cost = current_cost
                    best_bundles = candidate_bundles
                    #print(f'two bundles : {best_bundles}')

    # Try to split into three bundles
    if len(merged_orders) > 2:
        three_partitions = filter_partitions(merged_orders, 3)
        for partition in three_partitions:
            candidate_bundles = []
            valid_partition = True
            for part in partition:
                part_volume = get_total_volume(all_orders, part)
                part_bundle = None
                for rider in all_riders:
                    if rider.available_number > 0 and part_volume <= rider.capa:
                        for shop_pem in permutations(part):
                            for dlv_pem in permutations(part):
                                feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                                if feasibility_check == 0:
                                    total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                                    part_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), part_volume, total_dist)
                                    part_bundle.update_cost()
                                    candidate_bundles.append(part_bundle)
                                    break
                            if part_bundle:
                                break
                    if part_bundle:
                        break
                if not part_bundle:
                    valid_partition = False
                    break

            if valid_partition and len(candidate_bundles) == 3:
                current_cost = evaluate_bundles(candidate_bundles)
                if current_cost < min_total_cost:
                    min_total_cost = current_cost
                    best_bundles = candidate_bundles
                    #print(f'three bundles : {best_bundles}')

    return best_bundles

# Simulated Annealing을 사용하여 번들을 최적화하는 함수
def simulated_annealing(all_bundles, K, dist_mat, all_orders, all_riders, timelimit=60, initial_temp=100, cooling_rate=0.99):
    current_solution = all_bundles  # 현재 해를 초기 해로 설정
    current_cost = sum(bundle.cost for bundle in all_bundles) / K  # 초기 해의 비용 계산
    best_solution = current_solution[:]  # 초기 해를 최적 해로 설정
    best_cost = current_cost  # 초기 해의 비용을 최적 비용으로 설정
    temperature = initial_temp  # 초기 온도 설정

    if len(current_solution) > 1:  # 번들이 2개 이상일 때만 수행
        i, j = random.sample(range(len(current_solution)), 2)  # 무작위로 두 번들을 선택
        selected_bundles = [current_solution[i], current_solution[j]]
        new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, selected_bundles, all_riders)

        if new_bundles:  # 새로운 번들이 생성되었을 때
            new_cost = sum(bundle.cost for bundle in new_bundles) / K

            # 새로운 비용이 현재 비용보다 적거나, 확률적으로 수락할 때
            if new_cost < current_cost or random.uniform(0, 1) < math.exp((current_cost - new_cost) / temperature):
                current_solution = [bundle for k, bundle in enumerate(current_solution) if k != i and k != j] + new_bundles
                current_cost = new_cost

                if current_cost < best_cost:  # 새로운 해가 최적 해보다 나을 때
                    best_solution = current_solution[:]
                    best_cost = current_cost

    temperature *= cooling_rate  # 온도 감소

    return best_solution, best_cost  # 최적 해와 최적 비용 반환

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