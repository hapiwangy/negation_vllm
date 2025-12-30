import time
from pipeline import (
    step1_transformation,
    step2_answer_builder,
    step3_mask_generation, 
    step4_dataset_compiler
)

# log the result
import logging
from datetime import datetime

run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"app_{run_id}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
def main():
    logging.info("start of the process")

    steps = [
        ("Transformation", step1_transformation.run),
        ("Answer Construction", step2_answer_builder.run),
        ("Mask Generation", step3_mask_generation.run),
        ("Dataset Compilation", step4_dataset_compiler.run),
    ]

    t_total0 = time.perf_counter()
    times = {}

    print("Starting Pipeline...")
    logging.info("Starting Pipeline")

    for name, func in steps:
        logging.info(f"Starting process {name}")
        t0 = time.perf_counter()
        try:
            func() 
            status = "successful!"
        except Exception as e:
            print(f"Error in {name}: {e}")
            import traceback
            traceback.print_exc()
            break
        
        dt = time.perf_counter() - t0
        times[name] = dt
        print(f"{status} {name} finished in {dt:.3f}s\n")
        logging.info(f"{status} {name} finished in {dt:.3f}s\n")

    t_total = time.perf_counter() - t_total0

    logging.info("--- Summary ---")
    print("--- Summary ---")
    for name, dt in times.items():
        logging.info(f"{name}: {dt:.3f}s")
        print(f"{name}: {dt:.3f}s")
    logging.info(f"TOTAL: {t_total:.3f}s")
    print(f"TOTAL: {t_total:.3f}s")

if __name__ == "__main__":
    main()