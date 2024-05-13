import os
import csv
import pandas as pd
import pickle
import random
import joblib
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from SuperMarket import settings
from prediction.models import User
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
import subprocess


def admin_login(request):
    try:
        if request.method == "POST":
            email = request.POST["email"]
            password = request.POST["password"]
            user_object = User.objects.filter(user_email=email, user_password=password).first()
            print(f"User Email : {email}")
            print(f"User Password : {password}")
            if user_object:
                request.session['user_session_email'] = email
                return redirect('/orderid/')
            else:
                messages.error(request, "Invalid Username or Password")
                return redirect('/login/')
        else:
            return render(request, "login.html")
    except Exception as e:
        print(f"Error While Logging : {e}")
        return redirect('/login/')


def forgot(request):
    return render(request, "forgot_password.html")


def set_password(request):
    if request.method == "POST":

        otp = request.POST['otp']
        new_password = request.POST['npassword']
        confirm_password = request.POST['cpassword']

        if new_password == confirm_password:

            email = request.session['user_session_email']
            user_object = User.objects.filter(user_email=email, otp=otp, otp_used=0).first()

            if user_object:
                User.objects.filter(user_email=email).update(otp_used=1, user_password=new_password)
                return redirect("/login")
            else:
                messages.error(request, "Invalid OTP")
                return render(request, "set_password.html")

        else:
            messages.error(request, "New password & Confirm password does not match.")
            return render(request, "set_password.html")

    else:
        return redirect("/forgot_password")


def sendotp(request):
    new_otp = random.randint(10000, 99999)
    email = request.POST['email']

    request.session['user_session_email'] = email

    user_object = User.objects.filter(user_email=email).first()

    if user_object:
        User.objects.filter(user_email=email).update(otp=new_otp, otp_used=0)

        subject = 'OTP Verification'
        message = f"Your OTP Verification code : {str(new_otp)}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email, ]

        send_mail(subject, message, email_from, recipient_list)
        return render(request, 'set_password.html')

    else:
        messages.error(request, "Invalid Email")
        return render(request, "forgot_password.html")


def dashboard(request):
    if "user_session_email" in request.session:
        return render(request, "super_market_dashboard.html")
    else:
        return render(request, "login.html")




def predict_data(request):
    if "user_session_email" in request.session:
        try:
            oe = OrdinalEncoder()
            order_id = request.POST['order_id']
            year = request.POST['year']
            order_date = request.POST['order_date']
            ship_date = request.POST['ship_date']
            ship_mode = request.POST['ship_mode']
            customer_id = request.POST['customer_id']
            customer_name = request.POST['customer_name']
            segment = request.POST['segment']
            country = request.POST['country']
            city = request.POST['city']
            state = request.POST['state']
            postal_code = request.POST['postal_code']
            region = request.POST['region']
            product_id = request.POST['product_id']
            category = request.POST['category']
            sub_category = request.POST['sub_category']
            product_name = request.POST['product_name']
            sales = request.POST['sales']
            quantity = request.POST['quantity']
            discount = request.POST['discount']

            data = {
                'Order ID': order_id,
                'Year': year,
                'Order Date': order_date,
                'Ship Date': ship_date,
                'Ship Mode': ship_mode,
                'Customer ID': customer_id,
                'Customer Name': customer_name,
                'Segment': segment,
                'Country': country,
                'City': city,
                'State': state,
                'Postal Code': postal_code,
                'Region': region,
                'Product ID': product_id,
                'Category': category,
                'Sub-Category': sub_category,
                'Product Name': product_name,
                'Sales': sales,
                'Quantity': quantity,
                'Discount': discount
            }

            ss = pickle.load(open('prediction/data/standard_scaler.pkl', 'rb'))
            model = pickle.load(open('prediction/data/model_rfr.pkl', 'rb'))

            data = pd.DataFrame(data, index=[0])

            data['Order ID'] = data['Order ID'].str.split('-').str.get(2)
            data['Order ID'] = data['Order ID'].astype('int')

            data['Year'] = data['Year'].astype('int')

            data['Order Date'] = pd.to_datetime(data['Order Date'])
            data['Order_day'] = data['Order Date'].dt.day
            data['Order_month'] = data['Order Date'].dt.month
            data['Order_year'] = data['Order Date'].dt.year

            data['Ship Date'] = pd.to_datetime(data['Ship Date'])
            data['Ship_day'] = data['Ship Date'].dt.day
            data['Ship_month'] = data['Ship Date'].dt.month
            data['Ship_year'] = data['Ship Date'].dt.year

            data['Customer ID'] = data['Customer ID'].str.split('-').str.get(1)
            data['Customer ID'] = data['Customer ID'].astype('int')

            data['Postal Code'] = data['Postal Code'].astype('int')

            data['Product ID'] = data['Product ID'].str.split('-').str.get(2)
            data['Product ID'] = data['Product ID'].astype('int')

            oe_data = data[['Ship Mode', 'Segment', 'City', 'State', 'Region', 'Category', 'Sub-Category', 'Product Name']]

            oe = oe.fit_transform(data[['Ship Mode', 'Segment', 'City', 'State', 'Region', 'Category', 'Sub-Category', 'Product Name']])

            oe = pd.DataFrame(oe, columns=oe_data.columns)

            data = data.drop(columns=['Order Date', 'Ship Date', 'Ship Mode', 'Customer Name', 'Segment', 'Country', 'City', 'State','Region', 'Category', 'Sub-Category', 'Product Name'])

            data = data.join(oe)
            data = ss.transform(data)

            y_pred = model.predict(data)
            data = pd.DataFrame()
            return render(request, "super_market_dashboard.html", {"answer": y_pred})

        except Exception as e:
            messages.error(request, f"Error : {e}")
            return redirect('/dashboard/')

    else:
        return render(request, "login.html")


def user_logout(request):
    if 'user_session_email' in request.session:
        try:
            del request.session['user_session_email']
            return redirect("/login/")
        except Exception as e:
            print(f"Error While Logging out : {e}")
    else:
        return render(request, "login.html")


def test_power_bi(request):
    return redirect('https://app.powerbi.com/groups/me/reports/db5bb20c-03b6-439e-a1ed-3a286c53238d/ReportSection?experience=power-bi')


def open_powerbi_desktop(request):
    power_bi_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../prediction/data/SuperMarketPowerBI.pbix"))
    os.startfile(power_bi_path)
    return render(request, "super_market_dashboard.html")

from django.shortcuts import render
def upload_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            # Handle error: File is not a CSV file
            pass
        else:
            # Process the uploaded CSV file
            reader = csv.DictReader(csv_file.read().decode('latin-1').splitlines())
            for row in reader:
                order_id = row['Order ID']
                # Check if an object with the same Order_ID already exists
                existing_object = market_data.objects.filter(Order_ID=order_id).first()
                if existing_object:
                    # If an object with the same Order_ID exists, skip saving it again
                    continue
                # If no object with the same Order_ID exists, create and save a new object
                obj = market_data(
                    Order_ID=order_id,
                    Year=row['Year'],
                    Order_Date=row['Order Date'],
                    Ship_Date=row['Ship Date'],
                    Ship_Mode=row['Ship Mode'],
                    Customer_ID=row['Customer ID'],
                    Customer_Name=row['Customer Name'],
                    Segment=row['Segment'],
                    Country=row['Country'],
                    City=row['City'],
                    State=row['State'],
                    Postal_Code=row['Postal Code'],
                    Region=row['Region'],
                    Product_ID=row['Product ID'],
                    Category=row['Category'],
                    Sub_Category=row['Sub-Category'],
                    Product_Name=row['Product Name'],
                    Sales=row['Sales'],
                    Quantity=row['Quantity'],
                    Discount=row['Discount'],
                )
                obj.save()
            return render(request, 'success.html')
    return render(request, 'upload.html')
from .models import market_data


def orderid(request):
    return render(request,'orderid.html')

def orderdata(request):
    if "user_session_email" in request.session:
        
            if request.method=="POST":
                order_id = request.POST['order_id']

                marketData = market_data.objects.filter(Order_ID = order_id)
                # return render(request, "orderdata.html", {"data":marketData})
                
                for d in marketData:
                    Order_ID = d.Order_ID
                    Year = d.Year
                    Order_Date = d.Order_Date
                    Ship_Date = d.Ship_Date
                    Ship_Mode = d.Ship_Mode
                    Customer_ID = d.Customer_ID
                    Customer_Name = d.Customer_Name
                    Segment = d.Segment
                    Country = d.Country
                    City = d.City
                    State = d.State
                    Postal_Code = d.Postal_Code
                    Region = d.Region
                    Product_ID = d.Product_ID
                    Category = d.Category
                    Sub_Category = d.Sub_Category
                    Product_Name = d.Product_Name
                    Sales = d.Sales
                    Quantity = d.Quantity
                    Discount = d.Discount

                
















                oe = OrdinalEncoder()
                # order_id = request.POST['order_id']
                # year = request.POST['year']
                # order_date = request.POST['order_date']
                # ship_date = request.POST['ship_date']
                # ship_mode = request.POST['ship_mode']
                # customer_id = request.POST['customer_id']
                # customer_name = request.POST['customer_name']
                # segment = request.POST['segment']
                # country = request.POST['country']
                # city = request.POST['city']
                # state = request.POST['state']
                # postal_code = request.POST['postal_code']
                # region = request.POST['region']
                # product_id = request.POST['product_id']
                # category = request.POST['category']
                # sub_category = request.POST['sub_category']
                # product_name = request.POST['product_name']
                # sales = request.POST['sales']
                # quantity = request.POST['quantity']
                # discount = request.POST['discount']

                data = {
                    'Order ID': Order_ID,
                    'Year': Year,
                    'Order Date': Order_Date,
                    'Ship Date': Ship_Date,
                    'Ship Mode': Ship_Mode,
                    'Customer ID': Customer_ID,
                    'Customer Name': Customer_Name,
                    'Segment': Segment,
                    'Country': Country,
                    'City': City,
                    'State': State,
                    'Postal Code': Postal_Code,
                    'Region': Region,
                    'Product ID': Product_ID,
                    'Category': Category,
                    'Sub-Category': Sub_Category,
                    'Product Name': Product_Name,
                    'Sales': Sales,
                    'Quantity': Quantity,
                    'Discount': Discount
                }

                ss = pickle.load(open('prediction/data/standard_scaler.pkl', 'rb'))
                model = pickle.load(open('prediction/data/model_rfr.pkl', 'rb'))

                data = pd.DataFrame(data, index=[0])

                data['Order ID'] = data['Order ID'].str.split('-').str.get(2)
                data['Order ID'] = data['Order ID'].astype('int')

                data['Year'] = data['Year'].astype('int')

                data['Order Date'] = pd.to_datetime(data['Order Date'])
                data['Order_day'] = data['Order Date'].dt.day
                data['Order_month'] = data['Order Date'].dt.month
                data['Order_year'] = data['Order Date'].dt.year

                data['Ship Date'] = pd.to_datetime(data['Ship Date'])
                data['Ship_day'] = data['Ship Date'].dt.day
                data['Ship_month'] = data['Ship Date'].dt.month
                data['Ship_year'] = data['Ship Date'].dt.year

                data['Customer ID'] = data['Customer ID'].str.split('-').str.get(1)
                data['Customer ID'] = data['Customer ID'].astype('int')

                data['Postal Code'] = data['Postal Code'].astype('int')

                data['Product ID'] = data['Product ID'].str.split('-').str.get(2)
                data['Product ID'] = data['Product ID'].astype('int')

                oe_data = data[['Ship Mode', 'Segment', 'City', 'State', 'Region', 'Category', 'Sub-Category', 'Product Name']]

                oe = oe.fit_transform(data[['Ship Mode', 'Segment', 'City', 'State', 'Region', 'Category', 'Sub-Category', 'Product Name']])

                oe = pd.DataFrame(oe, columns=oe_data.columns)

                data = data.drop(columns=['Order Date', 'Ship Date', 'Ship Mode', 'Customer Name', 'Segment', 'Country', 'City', 'State','Region', 'Category', 'Sub-Category', 'Product Name'])

                data = data.join(oe)
                data = ss.transform(data)

                y_pred = model.predict(data)
                data = market_data.objects.filter(Order_ID = order_id)
                data = pd.DataFrame()
                return render(request, "orderdata.html", {"answer": y_pred,"data":marketData})

        
    else:
        return render(request, "login.html")