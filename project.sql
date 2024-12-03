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

CREATE TABLE Person (
    userName VARCHAR(50) PRIMARY KEY,
    password TEXT NOT NULL,
    fname VARCHAR(50),
    lname VARCHAR(50),
    email VARCHAR(100)
);

CREATE TABLE PersonPhone (
    userName VARCHAR(50),
    phone VARCHAR(15),
    FOREIGN KEY (userName) REFERENCES Person(userName)
);

CREATE TABLE DonatedBy (
    itemID INT,
    userName VARCHAR(50),
    donateDate DATE,
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (userName) REFERENCES Person(userName)
);

CREATE TABLE Role (
    roleID INT AUTO_INCREMENT PRIMARY KEY,
    rDescription TEXT
);

CREATE TABLE Act (
    userName VARCHAR(50),
    roleID INT,
    FOREIGN KEY (userName) REFERENCES Person(userName),
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
    FOREIGN KEY (supervisor) REFERENCES Person(userName),
    FOREIGN KEY (client) REFERENCES Person(userName)
);

CREATE TABLE ItemIn (
    itemID INT,
    orderID INT,
    found BOOLEAN,
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

CREATE TABLE Delivered (
    userName VARCHAR(50),
    orderID INT,
    status VARCHAR(50),
    date DATE,
    FOREIGN KEY (userName) REFERENCES Person(userName),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);
