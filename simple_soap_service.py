"""
Simple SOAP-like service using Flask
Alternative when spyne is not compatible
"""

from flask import Blueprint, request, Response
from models import db, User, Post, Comment
import xml.etree.ElementTree as ET
from xml.dom import minidom


simple_soap = Blueprint('simple_soap', __name__)


def create_soap_response(body_content):
    """Create SOAP envelope response"""
    envelope = ET.Element('soap:Envelope')
    envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')

    body = ET.SubElement(envelope, 'soap:Body')
    body.append(body_content)

    # Pretty print the XML
    rough_string = ET.tostring(envelope, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_soap_fault(fault_code, fault_string):
    """Create SOAP fault response"""
    envelope = ET.Element('soap:Envelope')
    envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')

    body = ET.SubElement(envelope, 'soap:Body')
    fault = ET.SubElement(body, 'soap:Fault')

    code = ET.SubElement(fault, 'faultcode')
    code.text = fault_code

    string = ET.SubElement(fault, 'faultstring')
    string.text = fault_string

    rough_string = ET.tostring(envelope, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def parse_soap_request(xml_data):
    """Parse SOAP request to extract method and parameters"""
    try:
        root = ET.fromstring(xml_data)

        # Find the method name (first child of Body)
        body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
        if body is None:
            return None, None

        # Get first child of body (the method)
        method_element = list(body)[0] if len(list(body)) > 0 else None
        if method_element is None:
            return None, None

        method_name = method_element.tag.split('}')[-1] if '}' in method_element.tag else method_element.tag

        # Extract parameters
        params = {}
        for child in method_element:
            param_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            params[param_name] = child.text

        return method_name, params

    except Exception as e:
        return None, None


@simple_soap.route('/soap', methods=['GET'])
def soap_wsdl():
    """Return WSDL description"""
    wsdl = '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://localhost:5000/soap"
             targetNamespace="http://localhost:5000/soap">

    <types>
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                   targetNamespace="http://localhost:5000/soap">
            
            <xs:element name="authenticateUser">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="username" type="xs:string"/>
                        <xs:element name="password" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
            
            <xs:element name="authenticateUserResponse">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="result" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
            
            <xs:element name="getAllUsers">
                <xs:complexType>
                    <xs:sequence/>
                </xs:complexType>
            </xs:element>
            
            <xs:element name="getAllUsersResponse">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="users" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
            
            <xs:element name="getStatistics">
                <xs:complexType>
                    <xs:sequence/>
                </xs:complexType>
            </xs:element>
            
            <xs:element name="getStatisticsResponse">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="stats" type="xs:string"/>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
            
        </xs:schema>
    </types>

    <message name="authenticateUserRequest">
        <part name="parameters" element="tns:authenticateUser"/>
    </message>
    <message name="authenticateUserResponse">
        <part name="parameters" element="tns:authenticateUserResponse"/>
    </message>
    
    <message name="getAllUsersRequest">
        <part name="parameters" element="tns:getAllUsers"/>
    </message>
    <message name="getAllUsersResponse">
        <part name="parameters" element="tns:getAllUsersResponse"/>
    </message>
    
    <message name="getStatisticsRequest">
        <part name="parameters" element="tns:getStatistics"/>
    </message>
    <message name="getStatisticsResponse">
        <part name="parameters" element="tns:getStatisticsResponse"/>
    </message>

    <portType name="BlogServicePortType">
        <operation name="authenticateUser">
            <input message="tns:authenticateUserRequest"/>
            <output message="tns:authenticateUserResponse"/>
        </operation>
        <operation name="getAllUsers">
            <input message="tns:getAllUsersRequest"/>
            <output message="tns:getAllUsersResponse"/>
        </operation>
        <operation name="getStatistics">
            <input message="tns:getStatisticsRequest"/>
            <output message="tns:getStatisticsResponse"/>
        </operation>
    </portType>

    <binding name="BlogServiceSOAPBinding" type="tns:BlogServicePortType">
        <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
        
        <operation name="authenticateUser">
            <soap:operation soapAction="authenticateUser"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        
        <operation name="getAllUsers">
            <soap:operation soapAction="getAllUsers"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        
        <operation name="getStatistics">
            <soap:operation soapAction="getStatistics"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>

    <service name="BlogService">
        <port name="BlogServiceSOAPPort" binding="tns:BlogServiceSOAPBinding">
            <soap:address location="http://localhost:5000/simple_soap/soap"/>
        </port>
    </service>

</definitions>'''

    return Response(wsdl, mimetype='text/xml')


@simple_soap.route('/soap', methods=['POST'])
def soap_handler():
    """Handle SOAP requests"""
    try:
        xml_data = request.get_data(as_text=True)
        method_name, params = parse_soap_request(xml_data)

        if not method_name:
            fault_xml = create_soap_fault('Client', 'Invalid SOAP request')
            return Response(fault_xml, mimetype='text/xml', status=400)

        # Handle different SOAP methods
        if method_name == 'authenticateUser':
            return handle_authenticate_user(params)
        elif method_name == 'getAllUsers':
            return handle_get_all_users()
        elif method_name == 'getStatistics':
            return handle_get_statistics()
        else:
            fault_xml = create_soap_fault('Client', f'Unknown method: {method_name}')
            return Response(fault_xml, mimetype='text/xml', status=400)

    except Exception as e:
        fault_xml = create_soap_fault('Server', f'Internal error: {str(e)}')
        return Response(fault_xml, mimetype='text/xml', status=500)


def handle_authenticate_user(params):
    """Handle user authentication"""
    try:
        username = params.get('username', '')
        password = params.get('password', '')

        if not username or not password:
            result = "Error: Username and password required"
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                result = f"Authentication successful for user: {username}"
            else:
                result = "Authentication failed: Invalid credentials"

        # Create response XML
        response = ET.Element('authenticateUserResponse')
        response.set('xmlns', 'http://localhost:5000/soap')

        result_elem = ET.SubElement(response, 'result')
        result_elem.text = result

        soap_response = create_soap_response(response)
        return Response(soap_response, mimetype='text/xml')

    except Exception as e:
        fault_xml = create_soap_fault('Server', f'Authentication error: {str(e)}')
        return Response(fault_xml, mimetype='text/xml', status=500)


def handle_get_all_users():
    """Handle get all users request"""
    try:
        users = User.query.all()

        users_info = []
        for user in users:
            users_info.append(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Posts: {len(user.posts)}")

        users_text = "; ".join(users_info) if users_info else "No users found"

        # Create response XML
        response = ET.Element('getAllUsersResponse')
        response.set('xmlns', 'http://localhost:5000/soap')

        users_elem = ET.SubElement(response, 'users')
        users_elem.text = users_text

        soap_response = create_soap_response(response)
        return Response(soap_response, mimetype='text/xml')

    except Exception as e:
        fault_xml = create_soap_fault('Server', f'Error getting users: {str(e)}')
        return Response(fault_xml, mimetype='text/xml', status=500)


def handle_get_statistics():
    """Handle get statistics request"""
    try:
        users_count = User.query.count()
        posts_count = Post.query.count()
        comments_count = Comment.query.count()

        stats_text = f"Blog Statistics: {users_count} users, {posts_count} posts, {comments_count} comments"

        # Create response XML
        response = ET.Element('getStatisticsResponse')
        response.set('xmlns', 'http://localhost:5000/soap')

        stats_elem = ET.SubElement(response, 'stats')
        stats_elem.text = stats_text

        soap_response = create_soap_response(response)
        return Response(soap_response, mimetype='text/xml')

    except Exception as e:
        fault_xml = create_soap_fault('Server', f'Error getting statistics: {str(e)}')
        return Response(fault_xml, mimetype='text/xml', status=500)