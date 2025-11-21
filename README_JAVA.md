# Quran Center Management System (Java Version)

This is the Java Spring Boot version of the Quran Center Management System, migrated from Flask.

## Prerequisites

*   Java 21 (JDK)
*   Maven 3.x

## Project Structure

*   `src/main/java/com/qurancenter/`: Java source code.
    *   `model/`: JPA Entities matching the SQLite database tables.
    *   `repository/`: Data access interfaces.
    *   `controller/`: Web controllers handling HTTP requests.
    *   `security/`: Spring Security configuration (supports existing Flask password hashes).
*   `src/main/resources/`: Configuration and static resources.
    *   `templates/`: Thymeleaf HTML templates (converted from Jinja2).
    *   `static/`: CSS, JS, Images, and Uploads.
    *   `application.properties`: Database and server configuration.

## Database

The application uses the existing SQLite database `quran_center.db` located in the project root.
The schema is automatically mapped using Hibernate.

## How to Run

1.  Open a terminal in the project root.
2.  Run the application using Maven:

    ```bash
    mvn spring-boot:run
    ```

3.  Access the application at `http://localhost:8080`.

## Login

You can log in using the existing users from the Python version. The password encoding logic has been adapted to verify Flask's PBKDF2 hashes.

## Development Notes

*   **Templates:** `login.html` has been fully converted to Thymeleaf. Other templates in `src/main/resources/templates/` may require further conversion from Jinja2 syntax (`{{ }}`) to Thymeleaf (`th:text`).
*   **Controllers:** `MainController` handles the basic routes. Add more controllers in `com.qurancenter.controller` to handle specific features (Students, Reports, etc.) following the pattern in `app.py`.
