package com.ewdev.parkitnow.viewModel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.ewdev.parkitnow.auth.FirebaseService
import com.ewdev.parkitnow.data.DayTime
import com.ewdev.parkitnow.data.ParkedCar
import com.ewdev.parkitnow.data.RelativeParkedCar
import com.ewdev.parkitnow.data.User
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch
import kotlin.collections.ArrayList

class ParkCarViewModel(application: Application) : AndroidViewModel(application) {

    private lateinit var user: User

    val leaveTime: MutableLiveData<DayTime> = MutableLiveData()
    val blockedCars: MutableLiveData<List<ParkedCar>> = MutableLiveData()

    val _blockedCars: ArrayList<ParkedCar> = ArrayList()


    init {
        val auth = FirebaseAuth.getInstance()

        viewModelScope.launch {
            user = FirebaseService.getUser(auth.currentUser!!.uid)!!
        }
    }

    fun onTimeSet(hourOfDay: Int, minute: Int) {
        leaveTime.value = DayTime(hourOfDay, minute)

        // TODO: make sure (now > date)
    }

    fun removeFromList(car: ParkedCar) {
        _blockedCars.remove(car)
        blockedCars.postValue(_blockedCars)
    }

    fun addCar(car: ParkedCar) {
        _blockedCars.add(car)
        retrieveCars()
    }

    fun retrieveCars() {
        blockedCars.postValue(_blockedCars)
    }

    fun parkCar() {
//        _blockedCars
//        leaveTime
        GlobalScope.launch {
            // TODO: commit changes

//            // 1. change queue(s)
//            _blockedCars
//                    .map { car -> car.queueId }
//                    .distinct()     // in case user introduces two cars that are part of the same queue

            // queues updated, I have the new(actually old) queueId
//            val queueId

            // 2. update cars
//            FirebaseService.updateCarQueue(userCar)
//            for (car in )

            // 3. update users (nah, better not)

            // TODO: ch


        }
    }

}