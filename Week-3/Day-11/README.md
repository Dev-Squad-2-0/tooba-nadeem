# Implementation Tasks

----

# Part 1 — Relationship Discovery
Before writing queries:

-	Identify the primary key of each table.
  - ## PKs:
      ### country
      country_id
      
      ### city
      city_id
      
      ### language
      language_id
      
      ### actor
      actor_id
      
      ### address
      address_id
      
      ### category
      category_id
    
      ### film
      film_id
      
      ### customer
      customer_id
      
      ### staff
      staff_id
      
      ### film_actor (composite key)
      actor_id, film_id
      
      ### film_category (composite key)
      film_id, category_id
      
      ### inventory
      inventory_id
    
      ### rental
      rental_id
      
      ### store
      store_id
      
      ### payment
      payment_id
---------

-	Identify the foreign keys.
  - ## FKs
  ### country
  nil
  
  ### city
  country_id
  
  ### language
  nil
  
  ### actor
  nil
  
  ### address
  city_id
  
  ### category
  nil

  ### film
  language_id
  
  ### customer
  address_id
  
  ### staff
  address_id
  
  ### film_actor
  nil
  
  ### film_category
  nil
  
  ### inventory
  film_id
  
  ### rental
  inventory_id, customer_id, staff_id
  
  ### store
  manager_id, address_id
  
  ### payment
  customer_id, staff_id, rental_id
------------------------
-	Draw a simple relationship diagram (hand-drawn or using pgAdmin).

I have attached the erd I got using pgAdmin 4

------------
# Part 2 — SQL JOIN Challenges
1.Display Customer Name, Email, City, and Country.
2.Display every payment with Customer Name, Film Title, and Amount Paid.
3.Display every payment with Customer Name, Film Title, and Amount Paid.
4.Find the Top 10 customers based on total amount spent.
5.Display each film with its Category and Rental Rate.
6.Find all actors who appeared in each film.
7.Count how many films belong to each category.
8.Which categories generated the highest revenue? (Hint: This requires joining multiple tables.)
9. Find customers who have rented more than 20 films.
10.Which cities generated the highest rental revenue?

# Bonus Challenge
Without looking at any online solution,
Determine the shortest path of table joins needed to answer:
“Which actor has generated the highest total rental revenue?”
There is no direct relationship between actor and payment, so students must identify the intermediate tables themselves.
