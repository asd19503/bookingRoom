from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from models.user import User
from models.booking_room import Booking
from cnnDatabase import db
from models.booking_name import Booking_name
import re
from datetime import datetime, timezone, timedelta
from write_logs import log_operation

user_bp = Blueprint('user', __name__, template_folder='templates')

def admin_required(f):
    """Decorator để kiểm tra quyền admin."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'Administrator':
            flash('Access denied! Admins only.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function

@user_bp.route('/admin_panel', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    """Hiển thị danh sách người dùng và booking với phân trang."""

    # Lấy số trang hiện tại từ query string
    user_logon = session.get('username')
    user_page = request.args.get('user_page', 1, type=int)  # Phân trang người dùng
    booking_page = request.args.get('booking_page', 1, type=int)  # Phân trang đặt phòng
    name_page = request.args.get('name_page', 1, type=int)  # Phân trang đặt phòng

    #Sort
    sort_by = request.args.get('sort_by', 'booking_id')  # Sắp xếp mặc định theo ID
    sort_order = request.args.get('sort_order', 'asc')  # Mặc định là sắp xếp tăng dần

    # Lấy giá trị tìm kiếm từ query string
    search_query = request.args.get('search', '')

    # Phân trang người dùng
    user_pagination = User.query.order_by(User.user_id).paginate(page=user_page, per_page=10)
    users = user_pagination.items

    is_date = re.match(r"^\d{2}/\d{2}/\d{4}$", search_query)

    if is_date:
        try:
            # Chuyển đổi chuỗi ngày sang đối tượng datetime
            search_date = datetime.strptime(search_query, "%d/%m/%Y").date()
            search_date_str = search_date.strftime("%d/%m/%Y")
            booking_query = Booking.query.filter(Booking.reservation_date == search_date_str)
        except ValueError:
            # Nếu xảy ra lỗi khi chuyển đổi, bỏ qua tìm kiếm theo ngày
            booking_query = Booking.query
    elif search_query:
        # Nếu không phải ngày, tìm kiếm theo tên phòng
        booking_query = Booking.query.filter(Booking.room_name.like(f"%{search_query}%"))
    else:
        # Không có tìm kiếm
        booking_query = Booking.query

    # Phân trang booking với sort

    if sort_order == 'asc':
        booking_query = booking_query.order_by(getattr(Booking, sort_by).asc())
    else:
        booking_query = booking_query.order_by(getattr(Booking, sort_by).desc())


    booking_pagination = booking_query.order_by(Booking.booking_id).paginate(
        page=booking_page, per_page=20
    )
    bookings = booking_pagination.items

    name_pagination = Booking_name.query.order_by(Booking_name.name_id).paginate(
        page=name_page, per_page = 10
    )
    names = name_pagination.items

    # Truyền dữ liệu phân trang vào template
    return render_template(
        'admin_panel.html',
        users=users,
        user_pagination=user_pagination,
        bookings=bookings,
        booking_pagination=booking_pagination,
        names=names,
        name_pagination = name_pagination,
        search_query=search_query
    )


@user_bp.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    # Lấy dữ liệu từ yêu cầu
    data = request.json

    # Tìm người dùng trong database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Cập nhật thông tin người dùng
    user.firstname = data.get('firstname', user.firstname)
    user.lastname = data.get('lastname', user.lastname)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    user.password = data.get('password', user.password)  # Lưu ý: Hash mật khẩu trước khi lưu

    # Lưu thay đổi vào database
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/update_status/<int:user_id>', methods=['POST'])
def update_status(user_id):
    # Lấy dữ liệu từ yêu cầu
    data = request.json
    new_status = data.get('status')

    # Tìm người dùng trong database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Cập nhật trạng thái
    user.user_status = new_status

    # Lưu thay đổi vào database
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/add_user', methods=['POST'])
def add_user():
    # Lấy dữ liệu từ form
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    email = request.form['email']
    role = request.form['role']
    firstname = request.form.get('firstname', '')
    lastname = request.form.get('lastname', '')

    # Kiểm tra mật khẩu trùng khớp
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

    # Kiểm tra username hoặc email đã tồn tại
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400

    # Thêm user vào database
    new_user = User(
        username=username,
        password=password,  # Lưu ý: Hash mật khẩu trước khi lưu
        email=email,
        role=role,
        firstname=firstname,
        lastname=lastname,
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/update_booking_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    """
    Cập nhật trạng thái isDeleted cho một booking và cập nhật date_deleted nếu cần.
    """
    user = None
    try:
        data = request.json
        new_status = data.get('isDeleted')
        user = data.get('loggedInUser','')
        # Tìm booking trong database
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404

        # Lưu trạng thái trước khi cập nhật (old_data)
        old_data = {
            "isDeleted": booking.isDeleted,
            "date_deleted": booking.date_deleted.isoformat() if booking.date_deleted else None
        }

        # Cập nhật trạng thái và ngày xóa
        booking.isDeleted = new_status
        if new_status:
            gmt_plus_7 = timezone(timedelta(hours=7))  # Tạo múi giờ GMT+7
            booking.date_deleted = datetime.now(gmt_plus_7)  # Cập nhật ngày xóa nếu isDeleted = True
        else:
            booking.date_deleted = None  # Xóa giá trị date_deleted nếu isDeleted = False

        # Ghi log cho thao tác UPDATE
        log_operation(
            table_name="booking",
            operation_type="UPDATE",
            user_name=user,  # Thay bằng user hiện tại (nếu có)
            record_id=booking_id,
            old_data=old_data,
            new_data={
                "isDeleted": booking.isDeleted,
                "date_deleted": booking.date_deleted.isoformat() if booking.date_deleted else None
            },
            additional_info="Booking status isDeleted updated successfully"
        )

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        log_operation(
            table_name="booking",
            operation_type="ERROR",
            user_name=user,  # Thay bằng user hiện tại (nếu có)
            record_id=booking_id,
            additional_info=f"Failed to update booking status: {e}"
        )
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/add_meeting', methods=['POST'])
def add_meeting():
    # Fetch data from the form
    meeting = request.form.get('meetingTitle')  # Safely fetch form data
    description = request.form.get('description')

    if not meeting :
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Check if the meeting already exists
    existing_meeting = Booking_name.query.filter(Booking_name.booking_name == meeting).first()
    if existing_meeting:
        return jsonify({'success': False, 'error': 'Meeting already exists'}), 400

    # Create new meeting object
    new_meeting = Booking_name(booking_name=meeting, description=description)

    # Attempt to add to the database
    try:
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Meeting added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/update_meeting_status/<int:name_id>', methods=['POST'])
def update_meeting_status(name_id):
    # Lấy dữ liệu từ yêu cầu
    data = request.json
    new_status = data.get('status')

    # Kiểm tra tính hợp lệ của new_status
    if new_status not in [True, False]:
        return jsonify({'success': False, 'error': 'Invalid status value. Must be True or False'}), 400

    # Tìm meeting trong database
    meeting = Booking_name.query.get(name_id)
    if not meeting:
        return jsonify({'success': False, 'error': 'Meeting not found'}), 404

    # Cập nhật trạng thái
    meeting.isActive = new_status

    # Lưu thay đổi vào database
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Meeting status updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error', 'details': str(e)}), 500


@user_bp.route('/update_meeting/<int:name_id>', methods=['POST'])
def update_meeting(name_id):
    # Lấy dữ liệu từ yêu cầu
    data = request.json

    # Kiểm tra dữ liệu đầu vào
    if not data or 'description' not in data:
        return jsonify({'success': False, 'error': 'Invalid input data'}), 400

    # Tìm cuộc họp trong database
    meeting = Booking_name.query.get(name_id)
    if not meeting:
        return jsonify({'success': False, 'error': 'Meeting not found'}), 404

    # Cập nhật thông tin mô tả
    description = data.get('description')
    if description:
        if len(description) > 100:
            return jsonify({'success': False, 'error': 'Description is too long (max 100 characters)'}), 400
        meeting.description = description

    # Lưu thay đổi vào database
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Meeting updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error', 'details': str(e)}), 500