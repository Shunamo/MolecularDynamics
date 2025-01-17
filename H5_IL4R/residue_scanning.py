import os
import time
import subprocess

top_50_directory = "/home/shkim/H5_IL4R/haddock_H5_IL4R/prep_files/new/H5_IL4R_1"
residue_scan_results_dir = "./residue_scanning_result/new/H5_IL4R_1"
check_results="/home/shkim/H5_IL4R/haddock_H5_IL4R/residue_scanning_result/existing_structures"
os.makedirs(residue_scan_results_dir, exist_ok=True)

# Schrodinger 체인 정보 및 변이 리스트
H5_chain = 'B'
mutations = """
B:104 ARG
B:108 ARG
B:108 TYR
B:110 ARG
B:110 TYR
"""
num_cores = 40  
def perform_residue_scanning(maegz_file, result_csv_path):
    """Residue Scanning을 수행하는 함수"""
    maegz_base = os.path.splitext(os.path.basename(maegz_file))[0]
    
    mutation_file_name = os.path.join(residue_scan_results_dir, f"{maegz_base}_mutations.txt")
    with open(mutation_file_name, 'w') as mut_file:
        mut_file.write(mutations)
    
    script_content = f"""#!/bin/bash
$SCHRODINGER/run residue_scanning_backend.py -fast -jobname {maegz_base}_residue_scan -res_file {mutation_file_name} -refine_mut prime_residue -calc hydropathy,rotatable,vdw_surf_comp,sasa_polar,sasa_nonpolar,sasa_total -dist 0.00 {maegz_file} -receptor_asl 'NOT (chain.n {H5_chain})' -add_res_scan_wam -HOST localhost:{num_cores} -TMPLAUNCHDIR
"""
    script_filename = os.path.join(residue_scan_results_dir, f"residue_scanning_{maegz_base}.sh")
    
    with open(script_filename, 'w') as sh_file:
        sh_file.write(script_content)
    subprocess.run(["chmod", "+x", script_filename])
    
    try:
        process = subprocess.run([script_filename], check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"Successfully processed {maegz_file}")
        print(process.stdout.decode())
        
        print(f"Checking for result CSV in: {result_csv_path}")
        for _ in range(60):
            if os.path.exists(result_csv_path):
                print(f"Result CSV found: {result_csv_path}")
                break
            time.sleep(1)
        
        if not os.path.exists(result_csv_path):
            print(f"Error: {maegz_file} residue scanning likely failed. CSV not found at {result_csv_path}.")
            return False
        
        print(f"Removing processed maegz file: {maegz_file}")
        os.remove(maegz_file)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {maegz_file}: {e.stderr.decode()}")
        return False
    finally:
        print(f"Cleaning up: {script_filename}, {mutation_file_name}")
        os.remove(script_filename)
        os.remove(mutation_file_name)

# CSV 파일없는 구조 확인
remaining_files = [f for f in os.listdir(top_50_directory) if f.endswith(".maegz")]

failed_files = []

print("Checking for missing CSV files...")

for filename in remaining_files:
    maegz_base = os.path.splitext(filename)[0]
    result_csv = f"{maegz_base}_residue_scan-results.csv"
    result_csv_path = os.path.join(check_results, result_csv)
    if not os.path.exists(result_csv_path):
        print(f"Missing CSV for structure: {filename}")
        failed_files.append(filename)
    else:
        print(f"CSV already exists for structure: {filename}, skipping residue scanning.")

# 실패한 파일에 대해서만 
while failed_files:
    print(f"Remaining structures to process: {len(failed_files)}")
    print(f"Structures left to process: {failed_files}")
    
    filename = failed_files.pop(0)
    maegz_file_path = os.path.join(top_50_directory, filename)
    result_csv_path = os.path.join(residue_scan_results_dir, f"{os.path.splitext(filename)[0]}_residue_scan-results.csv")
    
    success = perform_residue_scanning(maegz_file_path, result_csv_path)
    if not success:
        print(f"Retrying Residue Scanning for {filename}")
        failed_files.append(filename)  # 실패한 경우 다시 리스트에 추가
    
    if not failed_files:
        print("All residue scanning operations completed successfully.")
    else:
        print("Some residue scanning operations failed. Retrying...")
        time.sleep(60) 