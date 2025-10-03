import sys
import xml.etree.ElementTree as ET
import csv
import os

def parse_result(result_file):
    tree = ET.parse(result_file)
    root = tree.getroot()

    # Host.IO_Flow
    host_flow = root.find(".//Host.IO_Flow")
    iops = iops_r = iops_w = resp_time = None
    if host_flow is not None:
        iops = host_flow.findtext("IOPS")
        iops_r = host_flow.findtext("IOPS_Read")
        iops_w = host_flow.findtext("IOPS_Write")
        resp_time = host_flow.findtext("Device_Response_Time")

    # SSDDevice.IO_Stream
    io_stream = root.find(".//SSDDevice.IO_Stream")
    read_lat = write_lat = None
    if io_stream is not None:
        read_lat = io_stream.findtext("Average_Read_Transaction_Turnaround_Time")
        write_lat = io_stream.findtext("Average_Write_Transaction_Turnaround_Time")

    return {
        "Scenario_File": os.path.basename(result_file),
        "Device_Response_Time(us)": resp_time,
        "Avg_Read_Latency(ns)": read_lat,
        "Avg_Write_Latency(ns)": write_lat,
        "IOPS": iops,
        "IOPS_Read": iops_r,
        "IOPS_Write": iops_w,
    }

def parse_workload(workload_file):
    tree = ET.parse(workload_file)
    root = tree.getroot()

    scenarios = []
    for i, sc in enumerate(root.findall(".//IO_Scenario"), start=1):
        syn = sc.find("IO_Flow_Parameter_Set_Synthetic")
        trc = sc.find("IO_Flow_Parameter_Set_Trace_Based")
        params = {"Scenario_ID": i}

        if syn is not None:
            params["Type"] = "Synthetic"
            params["Read_Percentage"] = syn.findtext("Read_Percentage")
            params["Queue_Depth"] = syn.findtext("Average_No_of_Reqs_in_Queue")
            params["Seed"] = syn.findtext("Seed")
        elif trc is not None:
            params["Type"] = "Trace"
            params["Trace_File"] = trc.findtext("File_Path")
            params["Percentage_To_Be_Executed"] = trc.findtext("Percentage_To_Be_Executed")
        scenarios.append(params)

    return scenarios

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 analyze_mqsim.py workload.xml results.csv workload_scenario_*.xml")
        sys.exit(1)

    workload_file = sys.argv[1]
    output_file = sys.argv[2]
    result_files = sys.argv[3:]

    workload_params = parse_workload(workload_file)
    results = []

    for idx, rf in enumerate(result_files, start=1):
        res = parse_result(rf)
        if idx <= len(workload_params):
            res.update(workload_params[idx-1])  # 合併對應 scenario 的參數
        results.append(res)

    # 輸出 CSV
    fieldnames = ["Scenario_ID","Scenario_File","Type","Read_Percentage","Queue_Depth",
                  "Seed","Trace_File","Percentage_To_Be_Executed",
                  "Device_Response_Time(us)","Avg_Read_Latency(ns)","Avg_Write_Latency(ns)",
                  "IOPS","IOPS_Read","IOPS_Write"]

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Results saved to {output_file}")

