from datetime import datetime, timedelta

def calculate_duration(start_time, end_time):
    """Calculate duration in minutes between two time strings"""
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')

        duration = end - start
        if duration.total_seconds() < 0:  # If end time is on next day
            duration = duration + timedelta(days=1)

        return int(duration.total_seconds() / 60)
    except:
        return 0

def get_shift_options():
    return ['Morning', 'Afternoon', 'Night']

def get_line_options():
    return [f'Line {i}' for i in range(1, 31)]  # Lines 1-30

def get_equipment_options():
    standard_options = [
        'Blowmould', 'Mixer', 'Variopac', 'Coding Machine',
        'Conveyor', 'Packaging Machine', 'Labeler',
        'Filler', 'Capper', 'Palletizer'
    ]
    return standard_options + ['Other']

def get_issue_type_options():
    standard_options = [
        'Production', 'Mechanical', 'Electrical', 'Operational',
        'Quality', 'Material Shortage'
    ]
    return standard_options + ['Other']

def format_downtime_summary(records, production_data):
    """Format downtime summary for sharing"""
    # Filter records for selected date and line
    filtered_records = [r for r in records 
                       if r[1] == production_data['date'] 
                       and r[3] == production_data['line']
                       and r[6] >= 10]  # records where duration >= 10 minutes

    summary = f"Production Summary\n"
    summary += f"Date: {production_data['date']}\n"
    summary += f"Line: {production_data['line']}\n"
    summary += f"Shift: {production_data['shift']}\n"
    summary += f"Packs Produced: {production_data['packs_produced']}\n\n"

    if filtered_records:
        summary += "Major Downtimes (≥10 minutes):\n"
        for record in filtered_records:
            summary += f"- {record[7]} ({record[6]} mins): {record[9]}\n"
    else:
        summary += "No major downtimes recorded for this line and date.\n"

    return summary