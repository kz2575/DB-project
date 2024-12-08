DROP TABLE IF EXISTS Delivered;
DROP TABLE IF EXISTS ItemIn;
DROP TABLE IF EXISTS Ordered;
DROP TABLE IF EXISTS Piece;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Act;
DROP TABLE IF EXISTS Role;
DROP TABLE IF EXISTS DonatedBy;
DROP TABLE IF EXISTS PersonPhone;
DROP TABLE IF EXISTS Person;
DROP TABLE IF EXISTS Item;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS user;

CREATE TABLE user
(
    cid        INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50)        NOT NULL,
    last_name  VARCHAR(50)        NOT NULL,
    username   VARCHAR(50) UNIQUE NOT NULL,
    password   VARCHAR(1000)      NOT NULL,
    email   VARCHAR(4000)      NOT NULL
);

CREATE TABLE Category (
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    catNotes TEXT,
    PRIMARY KEY (mainCategory, subCategory)
);

CREATE TABLE Item (
    itemID INT AUTO_INCREMENT PRIMARY KEY,
    iDescription TEXT,
    photo TEXT,
    color VARCHAR(30),
    isNew BOOLEAN,
    hasPieces BOOLEAN,
    material VARCHAR(50),
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    FOREIGN KEY (mainCategory, subCategory) REFERENCES Category(mainCategory, subCategory)
);


CREATE TABLE PersonPhone (
    userName VARCHAR(50),
    phone VARCHAR(15),
    PRIMARY KEY (userName, phone),
    FOREIGN KEY (userName) REFERENCES User(userName)
);

CREATE TABLE DonatedBy (
    itemID INT,
    userName VARCHAR(50),
    donateDate DATE,
    PRIMARY KEY (itemID, userName),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (userName) REFERENCES User(userName)
);

CREATE TABLE Role (
    roleID INT AUTO_INCREMENT PRIMARY KEY,
    rDescription TEXT
);

CREATE TABLE Act (
    userName VARCHAR(50),
    roleID INT,
    FOREIGN KEY (userName) REFERENCES User(userName),
    FOREIGN KEY (roleID) REFERENCES Role(roleID)
);

CREATE TABLE Location (
    roomNum VARCHAR(20),
    shelfNum VARCHAR(20),
    shelfDescription TEXT,
    PRIMARY KEY (roomNum, shelfNum)
);

CREATE TABLE Piece (
    itemID INT,
    pieceNum INT,
    pDescription TEXT,
    length FLOAT,
    width FLOAT,
    height FLOAT,
    roomNum VARCHAR(20),
    shelfNum VARCHAR(20),
    pNotes TEXT,
    PRIMARY KEY (itemID, pieceNum),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (roomNum, shelfNum) REFERENCES Location(roomNum, shelfNum)
);

CREATE TABLE Ordered (
    orderID INT AUTO_INCREMENT PRIMARY KEY,
    orderDate DATE,
    orderNotes TEXT,
    supervisor VARCHAR(50),
    client VARCHAR(50),
    FOREIGN KEY (supervisor) REFERENCES User(userName),
    FOREIGN KEY (client) REFERENCES User(userName)
);

CREATE TABLE ItemIn (
    itemID INT,
    orderID INT,
    found BOOLEAN,
    PRIMARY KEY (itemID, orderID),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

CREATE TABLE Delivered (
    userName VARCHAR(50),
    orderID INT,
    status VARCHAR(50),
    date DATE,
    PRIMARY KEY (userName, orderID),
    FOREIGN KEY (userName) REFERENCES User(userName),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

INSERT INTO Role (rDescription) VALUES ('client'), ('volunteer'), ('staff'), ('donor');

INSERT INTO Category (mainCategory, subCategory, catNotes)
VALUES
('mc1', 'sc1', 'Category Note 1'),
('mc1', 'sc2', 'Category Note 2'),
('mc2', 'sc1', 'Category Note 3'),
('mc2', 'sc2', 'Category Note 4');

INSERT INTO Location (roomNum, shelfNum, shelfDescription)
VALUES
(0, 0, 'Room 0 Shelf 0'),
(0, 1, 'Room 0 Shelf 1'),
(1, 0, 'Room 1 Shelf 0'),
(1, 1, 'Room 1 Shelf 1');

INSERT INTO Delivered (userName, orderID, status, date)
VALUES
    ('volunteer1', 1, 'Delivered', '2024-12-07'),
    ('volunteer1', 2, 'In Progress', '2024-12-08'),
    ('volunteer1', 3, 'Delivered', '2024-12-09');