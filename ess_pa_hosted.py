import os,time
import requests,json
from datetime import datetime,timedelta
import yagmail,dotenv
from twilio.rest import Client



def post_data(name,password):
    headers = {
        "Authorization": "Basic bXktdHJ1c3RlZC1jbGllbnQ6c2VjcmV0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "password",
        f"username": {name},
        f"password": {password}
    }
    url="https://ess.changepond.com/ESS-Java/oauth/token"
    try:
        for i in range(5):
            res=requests.post(url,headers=headers,data=data)
            response=res.json()
            access_token=response.get('access_token')
            if res.status_code==200:
                return access_token
            time.sleep(2)
    except Exception as e:
        print(e)
        print("Data not found")
        return None 
    

def get_details(access_token,name):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    url=f"https://ess.changepond.com/ESS-Java/api/emplyee/dashboard/{name}"
    for i in range(5):
        get_data=requests.get(url,headers=headers)
        if get_data.status_code==200:
            break
        time.sleep(2)
    get_response=get_data.json()
    if get_response['empAttenanceDet']['timeIn']:
        timein_timestamp=datetime.utcfromtimestamp(get_response['empAttenanceDet']['timeIn']/1000)+timedelta(hours=5,minutes=30)
        print(f"\ntime in: {timein_timestamp if timein_timestamp else 'Not punched in'}\ntime out: {get_response['empAttenanceDet']['timeOut'] if get_response['empAttenanceDet']['timeOut'] else 'Still not punched out'}")
        time_out=timein_timestamp+timedelta(hours=9)
        time_in=timein_timestamp.strftime('%H:%M:%S')
        return time_in,time_out.strftime('%H:%M:%S')
    else:
        return None

def get_particular_details(access,name):
    url="https://ess.changepond.com/ESS-Java/api/emplyee/empAttendanceReportDetailsSearch/"
    today=datetime.now().strftime('%d-%m-%Y')
    try:
        from_date=today.split('-')
        to_date=today.split('-')
        from_date_timestamp=int(datetime(int(from_date[2]),int(from_date[1]),int(from_date[0]),0,0).timestamp()*1000)
        to_date_timestamp=int(datetime(int(to_date[2]),int(to_date[1]),int(to_date[0]),0,0).timestamp()*1000)
    except:
        print("enter the date in valid date format")
        return
    
    # data={
    #     "timeIn":str(from_date_timestamp),
    #     "timeOut":str(to_date_timestamp)
    # }
    data={"empId":"",
          "timeIn":from_date_timestamp,
          "timeOut":to_date_timestamp,
          "authorised":"",
          "status":"",
          "supervisorEmpIds":""}

    # data=json.dumps(data)

    header={
        "Accept": "application/json",
        "Authorization":f"Bearer {access}",
        "Content-Type":"application/json",
        "Referer": "https://ess.changepond.com/"
    }

    response=requests.post(url,json=data,headers=header)

    data=response.json()

    final=[]
    header=["Date","Time In","Time Out","Totol Hours Worked"]
    for da in data:
        if da['timeIn'] or da["timeOut"]:
            try:
                time_in=datetime.utcfromtimestamp(da["timeIn"]/1000)+timedelta(hours=5,minutes=30)
                date=datetime.strftime(time_in,"%d-%m-%Y")
                time_in=datetime.strftime(time_in,"%H:%M:%S")
            except:
                time_in="None"
            try:
                time_out=datetime.utcfromtimestamp(da["timeOut"]/1000)+timedelta(hours=5,minutes=30)
                time_out=datetime.strftime(time_out,"%H:%M:%S")
                totol_hours_worked=da["hours"].strip()
            except:
                time_out,totol_hours_worked="None","None"
            final.append([date,time_in,time_out,totol_hours_worked])
        else:
            print("data not found")
    if final:
        print(tabulate(final,headers=header,tablefmt="fancy_grid"))

def get_shortfall_report(access):
    try:
        today=datetime.now()
        if today.month==1:
            prev_year=today.year-1
        else:
            prev_year=today.year
        start_date=datetime(prev_year,today.month-1,26).strftime('%Y-%m-%d')
        end_date=(today-timedelta(days=1)).strftime('%Y-%m-%d')
        from_date=start_date
        to_date=end_date
    except Exception as e:
        print(e)
        print('Please enter correct date format')
        return
    hours_url=f"https://ess.changepond.com/ESS-Java/api/emplyee/shortfallReportHours?fromDate={from_date}&toDate={to_date}"
    days_url=f"https://ess.changepond.com/ESS-Java/api/emplyee/shortfallReportDays?fromDate={from_date}&toDate={to_date}"
    header={
        "Accept": "application/json",
        "Authorization":f"Bearer {access}",
        "Content-Type":"application/x-www-form-urlencoded",
        "Referer": "https://ess.changepond.com/"
    }

    hours_response=requests.get(hours_url,headers=header)
    days_response=requests.get(days_url,headers=header)

    res=hours_response.json()[0]
    days_res=days_response.json()[0]
    employee_name=days_res.get('employeeName')
    worked_hours=res.get('totalEssWokingHours')
    totol_working_hours,totol_working_minutes,totol_seconds=map(int,res['totalEssWokingHours'].split(':'))
    actual_working_hours=int(res['actualWorkingHours'])
    or_time=timedelta(hours=totol_working_hours,minutes=totol_working_minutes,seconds=totol_seconds)
    extra_shortfall=or_time-timedelta(hours=actual_working_hours)
    short_fall_days=days_res.get('shortFallOfDays')
    short_fall_hours=res['totalEssShortfallHours']
    actual_days=days_res.get('presentDaysplusLeaves')
    worked_days=days_res.get('presentDays')
    on_leave=days_res.get('leavesCount')
    data=[str(data) for data in [actual_days,worked_days,on_leave,actual_working_hours,worked_hours,short_fall_days,short_fall_hours,extra_shortfall]]
    final_data=f'''Actual days: {data[0]}\nWorked days: {data[1]}\nLeave days: {data[2]}\nTotal working hours: {data[3]}\nWorked hours: {data[4]}\nShort fall days: {data[5]}\nShort fall hours: {data[6]}\nExtra short fall: {data[7]}'''
    print(final_data)
    return final_data,employee_name,from_date,to_date
    
def send_email(to_email,data,time_in,time_out):
    email='devanathan.pain@gmail.com'
    dotenv.load_dotenv()
    app_key=os.getenv("EMAIL_KEY")
    yagmail.register(email,app_key)
    yag=yagmail.SMTP(email)
    if data:
        format=f'''Hi {data[1]},
                
                Below you can find your ess report from {data[2]} to {data[3]}

                {data[0]}

                    Today you logged in at {time_in} and you should logout at {time_out}

                    Regards,
                    Deva '''
    else:
        format='''
            Today you didn\'t punched in

            Thanks & regards,
            Deva
'''
    yag.send(to=to_email,subject='Ess report',contents=format)
    print('mail sent successfully')

def send_whatsapp_msg(data,time_in,time_out):
    dotenv.load_dotenv()
    account_sid = os.getenv('ACCOUNT_SID')
    auth_token = os.getenv('TWILLO_AUTH_TOKEN')

    client = Client(account_sid, auth_token)

    if data:
        body=f'''Hi {data[1]}

    You can find your ESS report below from {data[2]} 📆 to {data[3]} 📆

    Today will be  good day for you ❤️

    Thank you 😊

    {data[0]}

    Today you logged in at {time_in} and you should logout at {time_out}

    '''
    else:
        body='Today you didn\'t punched in' 

    phone_number=os.getenv('PHONE_NUMBER')
    message = client.messages.create(
        body=body,
        from_='whatsapp:+14155238886',  
        to=f'whatsapp:+91{phone_number}'     
    )

    print("Message SID:", message.sid)
    print("Message sent successfully..")

    return



if __name__=="__main__":
    dotenv.load_dotenv()
    name='4559'
    password=os.getenv('ESS_PASSWORD')
    access=post_data(name=name,password=password)
    email='devanathan640@gmail.com'
    if access:
        if get_details(access,name):
            time_in,time_out=get_details(access,name)
            all_data=get_shortfall_report(access)
            send_email(email,all_data,time_in,time_out)
            send_whatsapp_msg(all_data,time_in,time_out)
        else:
            send_email(to_email=email,data=None,time_in=None,time_out=None)
            send_whatsapp_msg(data=None,time_in=None,time_out=None)
    else:
        print("Data not found")
