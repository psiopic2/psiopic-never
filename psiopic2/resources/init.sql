--- Create initial user ---

INSERT INTO user 
  (user_id,user_name,user_password,user_email,user_token,user_registration,user_newpassword) 
  VALUES 
  (
    1,
    'Admin',
    ':pbkdf2:sha256:10000:128:z6MSD/LNN3prz1ig8W40tg==:Kbgio2Xqqebibf56+D3rS+pSoZt6+VEPWryAatH5xzjAe6/kJ8SoppzgyRPjkuil6TtLW+a0agFhUTk+k1rDIzchGDkeErv1zNVV8KKRH9B7x1Itv2PUAYDSYgg2XzJINSJ3PEPZJ3tVnz/fT5YiakRv5VJJ8SVHgQVy5AvlDiI=', 
    'admin@admin.com', 
    'e668f0608e606d0a023150c8ca44bda5', 
    20150829030838,
    'nope'
  );

INSERT INTO user_groups (ug_user, ug_group) VALUES (1, 'bureaucrat');
INSERT INTO user_groups (ug_user, ug_group) VALUES (1, 'sysop');

--- ALTER TABLE `page` CHANGE COLUMN `page_id` `page_id` INT(10) UNSIGNED NOT NULL COMMENT '' ;---

--- ALTER TABLE `page` DROP PRIMARY KEY; ---
