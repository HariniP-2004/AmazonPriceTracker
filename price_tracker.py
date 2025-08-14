import time
from bs4 import BeautifulSoup
import requests
import smtplib
import mysql.connector
from tkinter import *
from tkinter import ttk, Canvas, simpledialog
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk

# SQL CONNECTOR
mydb = mysql.connector.connect(host="localhost", user=USER, passwd=PASSWORD, database="PriceTracker")
cursor = mydb.cursor()

# UI SETUP
window = Tk()
window.title("Amazon Price Tracker")
window.minsize(width=1000, height=550)
window.config(background="black")
pil_image = Image.open("black_bg.jpg")
window_width = 1000
window_height = 550
resized_image = pil_image.resize((window_width, window_height), Image.LANCZOS)
background_image = ImageTk.PhotoImage(resized_image)
canvas = Canvas(window, width=1000, height=550)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=background_image, anchor="nw")

# Caption Label
caption_label = Label(text="STAY AHEAD OF THE SALES !!!", font=("Futura", 26, "bold"), bg="black", foreground="white")
caption_label.place(relx=0.5, rely=0.05, anchor="center")
sub_cap_label = Label(text="Unlock the Best Deals! 🏷💰", font=("Gill Sans", 20), background="black",
                          foreground="light sky blue")
sub_cap_label.place(x=400, y=100)

# Get URL
input_url = Entry(width=50, background="grey")
url_label = Label(text="Enter product URL : ", font=("Helvetica", 20, "italic"), background="black", foreground="white")
url_label.place(x=190, y=210)
input_url.place(x=410, y=210)



def click_add():
    url = input_url.get()
    add_product(url)


def add_product(url):
    try:
        ua_header = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        al_header = "en-US,en;q=0.9"
        response = requests.get(f"{url}", headers={"User-Agent": ua_header, "Accept-Language": al_header},
                                allow_redirects=True)
        soup = BeautifulSoup(response.content, "lxml")
        product_title = soup.find(name="span", id="productTitle").get_text().strip()
        price = soup.find(class_="a-offscreen").get_text()
        price_without_currency = price.split("$")[1]
        price_as_float = float(price_without_currency.replace(',', ''))

        sql = "INSERT INTO Products(ProductName, ProductURL) VALUES (%s, %s)"
        values = (product_title, url)
        cursor.execute(sql, values)
        product_id = cursor.lastrowid
        timestamp_value = datetime.now().date()
        ins_price = "INSERT INTO PriceHistory(ProductID, Timestamp, Price) VALUES (%s, %s, %s)"
        price_values = (product_id, timestamp_value, price_as_float)
        cursor.execute(ins_price, price_values)

        prod_added_label = Label(text="Product added to your cart!", background="black", foreground="MistyRose2")
        prod_added_label.place(x=600, y=280)
        # Remove the label after 2 seconds (2000 milliseconds)
        window.after(2000, prod_added_label.destroy)
        mydb.commit()

        start_price_checking(product_id, url, 200, product_title)

        print("Values inserted successfully!")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch URL: {e}")
    except mysql.connector.Error as error:
        print("Error:", error)

def start_price_checking(product_id, url, initial_price, product_title):
    def price_check_loop(initial_price):
        while True:
            try:
                ua_header = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                al_header = "en-US,en;q=0.9"
                response = requests.get(f"{url}", headers={"User-Agent": ua_header, "Accept-Language": al_header},
                                        allow_redirects=True)
                soup = BeautifulSoup(response.content, "lxml")
                price = soup.find(class_="a-offscreen").get_text()
                price_without_currency = price.split("$")[1]
                price_as_float = float(price_without_currency.replace(',', ''))

                timestamp_value = datetime.now().date()
                ins_price = "INSERT INTO PriceHistory(ProductID, Timestamp, Price) VALUES (%s, %s, %s)"
                price_values = (product_id, timestamp_value, price_as_float)
                cursor.execute(ins_price, price_values)
                mydb.commit()

                # Check for price drop and send email if necessary
                if price_as_float < initial_price:
                    send_price_alert(product_title, price, url)
                    initial_price = price_as_float

                time.sleep(3600)  # Check every hour
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
            except mysql.connector.Error as error:
                print("Database error:", error)

    from threading import Thread
    Thread(target=price_check_loop, args=(initial_price,), daemon=True).start()


def send_price_alert(product_title, price, url):
    MY_EMAIL = "jan.wrk24@gmail.com"
    TO_EMAIL = "221001050@rajalakshmi.edu.in"
    MY_PASSWORD = "gpkfumdyxemmncwp"
    message = f"{product_title} is now {price}"

    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=MY_PASSWORD)
        connection.sendmail(from_addr=MY_EMAIL, to_addrs=TO_EMAIL,
                            msg=f"Subject:Amazon Price Alert!\n\n{message}\n{url}".encode("utf-8"))


add_button = Button(text="Add to cart", command=click_add)
add_button.place(x=450, y=350)
def fetch_data():
    cursor.execute('SELECT * FROM Products')
    rows = cursor.fetchall()
    return rows


def remove_product(product_id):
    try:
        cursor.execute('DELETE FROM PriceHistory WHERE ProductID=%s', (product_id,))
        cursor.execute('DELETE FROM Products WHERE ProductID=%s', (product_id,))
        mydb.commit()
        messagebox.showinfo("Info", f"Product with ID {product_id} has been removed.")
        refresh_table()
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Error occurred: {err}")


def prompt_remove_product():
    product_id = simpledialog.askinteger("Input", "Which product do you want to remove? Enter ProductId:")
    if product_id is not None:
        remove_product(product_id)


global product_tree
product_tree = None


def refresh_table():
    global product_tree
    if product_tree:
        for i in product_tree.get_children():
            product_tree.delete(i)
        rows = fetch_data()
        for row in rows:
            product_tree.insert('', END, values=row)


def display():
    clear()
    global product_tree
    #window.config(background="white")
    frame = Frame(window, borderwidth=2, relief="solid")
    frame.pack(fill=BOTH, expand=True)
    product_tree = ttk.Treeview(frame, columns=("ProductId", "ProductName", "ProductURL"), show='headings')

    product_tree.heading("ProductId", text="ProductId")
    product_tree.column("ProductId", width=5)

    product_tree.heading("ProductName", text="ProductName")
    product_tree.column("ProductName", width=100)

    product_tree.heading("ProductURL", text="ProductURL")
    product_tree.column("ProductURL", width=400)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=product_tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=product_tree.xview)

    product_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    product_tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    rows = fetch_data()
    for row in rows:
        product_tree.insert("", END, values=row)

    remove_prod = Button(text="Remove", command=prompt_remove_product)
    remove_prod.place(x=300, y=450)

    add_more = Button(text="Add more", command=lambda: display_initial_page(canvas))
    add_more.place(x=700, y=450)


def display_initial_page(canvas):
    clear()
    global caption_label, sub_cap_label, url_label, input_url, add_button, display_button, pil_image, window_height
    global resized_image, background_image, window_width
    pil_image = Image.open("black_bg.jpg")
    window_width = 1000
    window_height = 550
    resized_image = pil_image.resize((window_width, window_height), Image.LANCZOS)
    background_image = ImageTk.PhotoImage(resized_image)
    canvas = Canvas(window, width=1000, height=550)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=background_image, anchor="nw")

    caption_label = Label(text="STAY AHEAD OF THE SALES !!!", font=("Futura", 26, "bold"), bg="black",
                          foreground="white")
    caption_label.place(relx=0.5, rely=0.05, anchor="center")

    sub_cap_label = Label(text="Unlock the Best Deals! 🏷💰", font=("Gill Sans", 20), background="black",
                          foreground="light sky blue")
    sub_cap_label.place(x=400, y=100)

    url_label = Label(text="Enter product URL : ", font=("Helvetica", 20, "italic"), background="black",
                      foreground="white")
    url_label.place(x=190, y=210)

    input_url = Entry(width=50, background="grey")
    input_url.place(x=410, y=210)

    add_button = Button(text="Add to cart", command=click_add)
    add_button.place(x=450, y=350)

    display_button = Button(text="Display cart", bg="black", command=display)
    display_button.place(x=800, y=350)

    canvas.pack(fill="both", expand=True)


def clear():
    for widget in window.winfo_children():
        widget.destroy()


display_button = Button(text="Display cart", command=display)
display_button.place(x=800, y=350)

window.mainloop()

