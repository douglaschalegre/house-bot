from datetime import datetime, timedelta


def is_business_day(date):
    # Business days are Monday to Friday (0-4)
    return date.weekday() < 5


def is_today_fifth_business_day():
    today = datetime.today()
    start_of_month = today.replace(day=1)  # Set the date to the first of the month

    # List to hold the business days
    business_days = []

    # Iterate through the days of the month, starting from the first
    current_day = start_of_month
    while current_day.month == today.month:
        if is_business_day(current_day):
            business_days.append(current_day)
        current_day += timedelta(days=1)

    # Return the 5th business day (index 4 because it's zero-based)
    return True if len(business_days) == 5 else False
